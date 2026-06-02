import threading
import time
import cv2
import subprocess
import os
import logging

try:
    from picamera2 import Picamera2
except ImportError:
    Picamera2 = None

logger = logging.getLogger("AUDITORIA")

class ThreadedCamera:
    """Captura de vídeo (OpenCV/Picamera2)."""
    
    def __init__(self, source=0):
        self.source = source
        self.vid = None
        self.ret, self.frame = False, None
        self.started = False
        self.read_lock = threading.Lock()
        self.use_opencv = True 

    @staticmethod
    def detect_available_cameras():
        """Detecta câmeras CSI/USB."""
        cameras = []
        if Picamera2:
            try:
                picam_list = Picamera2.global_camera_info()
                for i, cam_info in enumerate(picam_list):
                    model = cam_info.get('Model', f'CSI Camera {i}')
                    cameras.append({'index': i, 'name': model, 'type': 'CSI', 'use_opencv': False})
            except Exception as e:
                logger.debug(f"Erro ao listar câmeras CSI: {e}")

        for i in range(16):
            dev_path = f"/dev/video{i}"
            if not os.path.exists(dev_path):
                continue
            try:
                cmd = f"v4l2-ctl --device={dev_path} --all"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if "Video Capture" in result.stdout and "Metadata" not in result.stdout:
                    cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
                    if cap.isOpened():
                        ret = cap.grab()
                        cap.release()
                        if ret:
                            cameras.append({
                                'index': i, 
                                'name': f'USB/V4L2 Camera {i}', 
                                'type': 'USB', 
                                'use_opencv': True
                            })
            except Exception:
                pass
        return cameras

    def start(self):
        """Inicializa hardware e thread de leitura."""
        with self.read_lock:
            if self.started: return self
            if self.source is None:
                available = self.detect_available_cameras()
                if available:
                    selected = next((c for c in available if c['type'] == 'CSI'), available[0])
                    self.source, self.use_opencv = selected['index'], selected['use_opencv']
            try:
                if self.use_opencv:
                    self.vid = cv2.VideoCapture(self.source, cv2.CAP_V4L2)
                    self.vid.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                elif Picamera2:
                    self.vid = Picamera2(camera_num=self.source)
                    config = self.vid.create_video_configuration(main={"size": (640, 480), "format": "BGR888"})
                    self.vid.configure(config)
                    self.vid.start()
                self.started = True
                self.thread = threading.Thread(target=self.update, args=(), daemon=True)
                self.thread.start()
            except Exception as e:
                logger.error(f"Falha ao iniciar câmera: {e}")
            return self

    def update(self):
        """Loop de atualização de frames."""
        while self.started:
            try:
                if self.use_opencv and self.vid:
                    self.vid.grab()
                    ret, frame = self.vid.retrieve()
                    if ret:
                        with self.read_lock: self.ret, self.frame = True, frame
                elif self.vid:
                    frame = self.vid.capture_array("main")
                    if frame is not None:
                        with self.read_lock: self.ret, self.frame = True, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            except: pass
            time.sleep(0.005)

    def get_frame(self):
        """Retorna frame recente."""
        with self.read_lock:
            if not self.started or self.frame is None: return False, None
            return self.ret, self.frame.copy()

    def stop(self):
        """Encerra captura e libera recursos."""
        with self.read_lock:
            if not self.started: return
            self.started = False
        if self.vid:
            try:
                if self.use_opencv: self.vid.release()
                else: self.vid.stop(); self.vid.close()
            except: pass
            self.vid = None
