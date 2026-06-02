import asyncio
import base64
import json
import time
import logging
import cv2
from fastapi import WebSocket, WebSocketDisconnect, status
from typing import Optional

from src.core import state
from src.config import VIGIA_API_KEY
from src.core.camera import ThreadedCamera
from src.utils.ws_utils import broadcast_ws

logger = logging.getLogger("AUDITORIA")
DETECTION_EXPIRY = 1.0

async def stream_frames_task():
    last_time = asyncio.get_event_loop().time()
    frame_count, fps = 0, 0
    
    while True:
        if not state.camera.started or not state.active_connections:
            await asyncio.sleep(0.5); continue
        
        ret, frame = state.camera.get_frame()
        if not ret: await asyncio.sleep(0.01); continue
        
        # Processa se a fila estiver vazia
        if state.inference_enabled and state.inference_queue.empty():
            try:
                state.inference_queue.put_nowait(frame.copy())
            except: pass

        frame_count += 1
        if frame_count >= 30:
            now = asyncio.get_event_loop().time()
            fps = frame_count / (now - last_time)
            last_time, frame_count = now, 0
            
        try:
            # Reduz visualização para 480x360
            preview_frame = cv2.resize(frame, (480, 360))
            frame_base64 = base64.b64encode(cv2.imencode(".jpg", preview_frame, [cv2.IMWRITE_JPEG_QUALITY, 50])[1]).decode("utf-8")
            
            faces_overlay = []
            with state.detections_lock:
                if state.latest_detections and (time.time() - state.latest_detections.get("timestamp", 0) < DETECTION_EXPIRY):
                    faces_overlay = state.latest_detections.get("faces", [])

            msg = json.dumps({
                "type": "VIDEO_FRAME", 
                "payload": {
                    "image": frame_base64, 
                    "fps": round(fps, 1),
                    "detections": faces_overlay
                }
            })
            await broadcast_ws(msg)
        except Exception as e:
            logger.debug(f"Erro no loop de frames: {e}")
            
        # Delay para evitar saturação
        await asyncio.sleep(0.03)

async def websocket_handler(websocket: WebSocket, token: Optional[str] = None):
    if token != VIGIA_API_KEY:
        await websocket.accept()
        await websocket.send_text(json.dumps({"type": "ERROR", "payload": "Acesso negado"}))
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    state.active_connections.append(websocket)
    state.connection_locks[websocket] = asyncio.Lock()
    
    available_cams = ThreadedCamera.detect_available_cameras()
    await websocket.send_text(json.dumps({"type": "SETTINGS_SYNC", "payload": {"cameras": available_cams, "inference_enabled": state.inference_enabled}}))
    
    if len(state.active_connections) == 1: 
        state.camera.start()
    
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "CONFIG_CHANGE":
                new_idx = msg["payload"].get("selected_camera")
                if new_idx is not None:
                    state.camera.stop(); state.camera.source = int(new_idx)
                    available = ThreadedCamera.detect_available_cameras()
                    for c in available:
                        if c['index'] == state.camera.source: 
                            state.camera.use_opencv = c['use_opencv']
                            break
                    state.camera.start()
            elif msg.get("type") == "SET_INFERENCE":
                state.inference_enabled = msg["payload"].get("enabled", True)
    except Exception:
        pass
    finally:
        if websocket in state.active_connections: 
            state.active_connections.remove(websocket)
        if websocket in state.connection_locks:
            del state.connection_locks[websocket]
        if not state.active_connections: 
            state.camera.stop()
