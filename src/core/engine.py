import time
import json
import base64
import logging
import asyncio
import numpy as np
import cv2
import os

from models import SCRFD, ArcFace
from src.database.face_db import FaceDatabase
from src.database.sqlite_db import save_to_history
from src.config import QDRANT_HOST, QDRANT_PORT, QDRANT_PATH, cipher_suite, HISTORY_COOLDOWN, AI_THRESHOLD, DETECTOR_MODEL, RECOGNIZER_MODEL, CAMERA_SOURCE, CAMERA_TYPE
from src.core import state
from src.utils.ws_utils import broadcast_ws_sync
from src.utils.normalization import normalize_name, normalize_cpf, normalize_birth_date

logger = logging.getLogger("AUDITORIA")

UI_UPDATE_COOLDOWN = 5 # segundos

def parse_face_metadata(name: str):
    """Extrai info do nome formatado."""
    if name is None:
        return "Desconhecido", "N/A", "N/A"
        
    # Garantir que name seja string se for array numpy
    if isinstance(name, np.ndarray):
        name = str(name.flatten()[0]) if name.size > 0 else "Unknown"
    else:
        name = str(name)

    if not name or name == "Unknown":
        return "Desconhecido", "N/A", "N/A"
        
    parts = [p.strip() for p in name.split("|")]
    
    # Caso 1: Formato padrão [CPF, NOME, NASC, ...]
    if len(parts) >= 2 and any(char.isdigit() for char in parts[0]):
        cpf = parts[0]
        nome = parts[1]
        nasc = parts[2] if len(parts) > 2 else "N/A"
    # Caso 2: Nome puro ou outro formato
    else:
        nome = parts[0]
        cpf = parts[1] if len(parts) > 1 else "N/A"
        nasc = parts[2] if len(parts) > 2 else "N/A"
        
    return nome, cpf, nasc

def sync_initial_faces():
    """Indexa faces de assets/faces (AES-256)."""
    faces_root = "./assets/faces"
    if not os.path.exists(faces_root) or not cipher_suite: return
    
    if state.face_db.index.ntotal > 0:
        logger.info(f"Banco já contém {state.face_db.index.ntotal} faces. Pulando sincronização inicial.")
        return

    logger.info("Iniciando sincronização CRIPTOGRAFADA de faces (AES-256)...")
    valid_extensions = ('.jpg', '.jpeg', '.png')
    
    for root, dirs, files in os.walk(faces_root):
        if "metadata.json" in files:
            try:
                meta_path = os.path.join(root, "metadata.json")
                with open(meta_path, "rb") as f:
                    encrypted_data = f.read()
                
                decrypted_data = cipher_suite.decrypt(encrypted_data)
                meta = json.loads(decrypted_data.decode())
                
                cpf = normalize_cpf(meta.get("cpf", "N/A"))
                nome = normalize_name(meta.get("nome", "Unknown"))
                nasc = normalize_birth_date(meta.get("nascimento", "N/A"))
                
                for filename in files:
                    if filename.lower().endswith(valid_extensions):
                        path = os.path.join(root, filename)
                        image = cv2.imread(path)
                        if image is None: continue
                        
                        bboxes, kpss = state.detector.detect(image, max_num=1)
                        if kpss is not None and len(kpss) > 0:
                            timestamp_suffix = int(time.time())
                            formatted_name = f"{cpf}|{nome}|{nasc}|{timestamp_suffix}"
                            embedding = np.array(state.recognizer.get_embedding(image, kpss[0]), dtype=np.float32)
                            state.face_db.add_faces_batch([embedding], [formatted_name])
                            logger.info(f"Decifrado e Sincronizado: {nome}")
            except Exception as e:
                logger.error(f"Falha ao decifrar pasta {root}: {e}")
    
    logger.info(f"Sincronização concluída. Total no banco: {state.face_db.index.ntotal}")

def inference_worker():
    """Thread de IA (Detecção/Reconhecimento)."""
    logger.info("Thread de IA iniciada com sucesso.")
    while not state.stop_event.is_set():
        try:
            if not state.inference_enabled or not state.active_connections:
                state.stop_event.wait(timeout=0.5)
                continue

            try:
                frame = state.inference_queue.get(timeout=1.0)
            except:
                continue

            # Processamento de IA
            t0 = time.time()

            # 480x360 para precisão/velocidade
            h_orig, w_orig = frame.shape[:2]
            frame_resized = cv2.resize(frame, (480, 360))
            scale_x, scale_y = w_orig / 480, h_orig / 360

            bboxes, kpss = state.detector.detect(frame_resized, max_num=0)
            t_det = time.time() - t0
            
            current_faces = []
            if bboxes is not None and len(bboxes) > 0:
                # Ajustar coordenadas de volta para o tamanho original
                bboxes[:, [0, 2]] *= scale_x
                bboxes[:, [1, 3]] *= scale_y
                
                if kpss is not None:
                    kpss[:, :, 0] *= scale_x
                    kpss[:, :, 1] *= scale_y

                t1 = time.time()
                embeddings = state.recognizer.get_embeddings_batch(frame, kpss)
                t_emb = time.time() - t1
                
                t2 = time.time()
                results = state.face_db.batch_search(embeddings, threshold=AI_THRESHOLD)
                t_search = time.time() - t2
                
                logger.info(f"PERF | Detecção (480x360): {t_det:.3f}s | Embeddings: {t_emb:.3f}s | Qdrant: {t_search:.3f}s | Faces: {len(bboxes)}")
                
                h, w = frame.shape[:2]
                for i, (name_raw, similarity) in enumerate(results):
                    # Forçar conversão para string para evitar ambiguidade do NumPy
                    if isinstance(name_raw, np.ndarray):
                        name = str(name_raw.flatten()[0]) if name_raw.size > 0 else "Unknown"
                    else:
                        name = str(name_raw) if name_raw is not None else "Unknown"

                    x1, y1, x2, y2 = map(int, bboxes[i][:4])
                    face_info = {
                        "box": [x1/w, y1/h, (x2-x1)/w, (y2-y1)/h],
                        "name": "Desconhecido" if name == "Unknown" else parse_face_metadata(name)[0],
                        "prob": float(similarity)
                    }
                    current_faces.append(face_info)

                    if name != "Unknown":
                        nome_v, cpf_v, nasc_v = parse_face_metadata(name)
                        metadata = {
                            "nome_completo": nome_v, "cpf": cpf_v, "data_nascimento": nasc_v,
                            "ia_prob": float(similarity), "camera_id": f"CAM-{state.camera.source}"
                        }
                        
                        person_key = cpf_v or nome_v
                        now = time.time()
                        
                        # Controle de atualização da interface (5 segundos)
                        should_update_ui = person_key not in state.last_ui_update or (now - state.last_ui_update[person_key] >= UI_UPDATE_COOLDOWN)
                        
                        if should_update_ui:
                            state.last_ui_update[person_key] = now
                            
                            # Tenta salvar no histórico permanente (HISTORY_COOLDOWN do .env)
                            history_entry = save_to_history(metadata, frame, state.last_history_save, HISTORY_COOLDOWN)
                            
                            x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
                            face_crop = frame[y1:y2, x1:x2]
                            
                            if face_crop.size > 0:
                                if history_entry:
                                    logger.info(f"IDENTIFICAÇÃO: {metadata['nome_completo']}")
                                
                                face_base64 = base64.b64encode(cv2.imencode(".jpg", face_crop, [cv2.IMWRITE_JPEG_QUALITY, 80])[1]).decode("utf-8")
                                msg = json.dumps({
                                    "type": "NEW_DETECTION",
                                    "payload": {
                                        "image": face_base64, 
                                        "metadata": metadata, 
                                        "history_id": history_entry["id"] if history_entry else None
                                    }
                                })
                                broadcast_ws_sync(msg)
            
            with state.detections_lock:
                state.latest_detections = {"faces": current_faces, "timestamp": time.time()}
            
            state.inference_queue.task_done()
        except Exception as e:
            logger.error(f"Erro na thread de inferência: {e}", exc_info=True)
            state.stop_event.wait(timeout=0.1)
    logger.info("Thread de IA encerrada.")

def init_engines():
    """Inicializa IA e Banco."""
    from src.core.camera import ThreadedCamera
    logger.info(f"Carregando detector: {DETECTOR_MODEL}")
    state.detector = SCRFD(model_path=DETECTOR_MODEL)
    
    logger.info(f"Carregando reconhecedor: {RECOGNIZER_MODEL}")
    state.recognizer = ArcFace(model_path=RECOGNIZER_MODEL)
    
    state.face_db = FaceDatabase(
        embedding_size=state.recognizer.embedding_size,
        host=QDRANT_HOST,
        port=QDRANT_PORT,
        path=QDRANT_PATH
    )
    camera_use_opencv = True
    if CAMERA_TYPE:
        camera_use_opencv = CAMERA_TYPE.strip().upper() != "CSI"
    state.camera = ThreadedCamera(source=CAMERA_SOURCE, use_opencv=camera_use_opencv)
    if CAMERA_SOURCE is not None:
        logger.info(f"Câmera forçada via .env: source={CAMERA_SOURCE}, tipo={'CSI' if not camera_use_opencv else 'USB'}")
    
    # Carrega banco com retry estendido
    max_retries = 30
    retry_delay = 5
    connected = False
    
    logger.info(f"Aguardando Qdrant estabilizar (Máximo {max_retries * retry_delay}s)...")
    for i in range(max_retries):
        if state.face_db.load(): 
            connected = True
            break
        logger.warning(f"Tentativa {i+1}/{max_retries}: Qdrant indexando 1.7M faces. Re-tentando em {retry_delay}s...")
        time.sleep(retry_delay)
    
    if not connected:
        logger.error("ERRO CRÍTICO: Qdrant não estabilizou. O reconhecimento será desabilitado.")
    
    sync_initial_faces()
