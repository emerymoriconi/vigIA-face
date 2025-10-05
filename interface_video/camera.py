import cv2
from picamera2 import Picamera2
import os

class Camera:
   
    def __init__(self, camera_index=0, use_opencv=False):
        """
        Args:
            camera_index: Índice da câmera
            use_opencv: True para USB/OpenCV, False para CSI/Picamera2
        """
        self.camera_index = camera_index
        self.use_opencv = use_opencv
        
        if use_opencv:
            # USB - OpenCV
            self.vid = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
            if not self.vid.isOpened():
                self.vid = cv2.VideoCapture(camera_index)
            if not self.vid.isOpened():
                raise RuntimeError(f"Erro ao abrir câmera USB {camera_index}")
            
            self.vid.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.vid.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
            print(f"Câmera {camera_index} inicializada com OpenCV (USB)")
        else:
            # CSI - Picamera2
            self.vid = Picamera2(camera_num=camera_index)
            self.video_config = self.vid.create_video_configuration(
                main={"size": (640, 480), "format": "BGR888"}
            )
            self.vid.configure(self.video_config)
            self.vid.start()
            print(f"Câmera {camera_index} inicializada com Picamera2 (CSI)")
    
    @staticmethod
    def detect_available_cameras():
        """Detecta todas câmeras disponíveis"""
        cameras = []
        
        # 1. Detecta CSI via Picamera2
        try:
            picam_list = Picamera2.global_camera_info()
            for i, cam_info in enumerate(picam_list):
                model = cam_info.get('Model', f'Camera {i}')
                # Só adiciona se for CSI real (ov/imx)
                if 'ov' in model.lower() or 'imx' in model.lower():
                    cameras.append({
                        'index': i,
                        'name': model,
                        'type': 'CSI',
                        'use_opencv': False
                    })
        except Exception as e:
            print(f"Erro ao detectar CSI: {e}")
        
        # 2. Detecta USB via video devices
        for i in range(20):
            device_path = f"/dev/video{i}"
            if not os.path.exists(device_path):
                continue
            
            # Verifica o nome do dispositivo
            try:
                name_path = f"/sys/class/video4linux/video{i}/name"
                if os.path.exists(name_path):
                    with open(name_path, "r") as f:
                        device_name = f.read().strip()
                    
                    # Detecta USB
                    if any(kw in device_name.lower() for kw in ['usb', 'uvc', 'hd camera', 'webcam']):
                        # Testa se OpenCV consegue abrir
                        cap = cv2.VideoCapture(i)
                        if cap.isOpened():
                            cap.release()
                            cameras.append({
                                'index': i,
                                'name': device_name,
                                'type': 'USB',
                                'use_opencv': True
                            })
            except:
                pass
        
        print(f"\nCâmeras detectadas: {len(cameras)}")
        for cam in cameras:
            print(f"  [{cam['index']}] {cam['type']}: {cam['name']}")
        
        return cameras

    def set_properties(self, width, height):
        if self.use_opencv:
            # USB/OpenCV
            self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            actual_w = int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
            return {'width': actual_w, 'height': actual_h, 'fps': 30}
        else:
            # CSI/Picamera2
            self.vid.stop()
            self.video_config = self.vid.create_video_configuration(
                main={"size": (width, height), "format": "BGR888"}
            )
            self.vid.configure(self.video_config)
            self.vid.start()
            return self.get_properties()

    def get_properties(self):
        if self.use_opencv:
            width = int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
        else:
            width, height = self.vid.camera_properties['PixelArraySize']
        
        return {'width': width, 'height': height, 'fps': 30}

    def get_frame(self):
        if self.use_opencv:
            # USB/OpenCV
            ret, frame = self.vid.read()
            if ret and frame is not None:
                return (True, frame)
            return (False, None)
        else:
            # CSI/Picamera2
            frame = self.vid.capture_array("main")
            if frame is not None:
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                return (True, frame_bgr)
            return (False, None)

    def release(self):
        try:
            if self.use_opencv:
                self.vid.release()
            else:
                self.vid.stop()
                self.vid.close()
            print(f"Câmera {self.camera_index} liberada")
        except Exception as e:
            print(f"Erro ao liberar câmera {self.camera_index}: {e}")