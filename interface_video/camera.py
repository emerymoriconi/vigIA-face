import cv2
from picamera2 import Picamera2

class Camera:
    def __init__(self, camera_num): 
        try:
            self.vid = Picamera2(camera_num=camera_num)
            self.is_picamera2 = True
            print(f"Câmera {camera_num} inicializada com Picamera2.")
            # Inicia Picamera2 com uma configuração padrão para poder setar propriedades depois
            self.video_config = self.vid.create_video_configuration(
                main={"size": (640, 480), "format": "BGR888"}
            )
            self.vid.configure(self.video_config)
            self.vid.start()
        except Exception as e:
            print(f"Não foi possível inicializar Picamera2 para a câmera {camera_num}: {e}. Tentando com OpenCV.")
            self.vid = cv2.VideoCapture(camera_num)
            self.is_picamera2 = False
            if not self.vid.isOpened():
                raise IOError(f"Não foi possível abrir a câmera {camera_num} com OpenCV.")
            print(f"Câmera {camera_num} inicializada com OpenCV.")
            # Define propriedades padrão para OpenCV
            self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    def set_properties(self, width, height):
        if self.is_picamera2:
            self.vid.stop()
            self.video_config = self.vid.create_video_configuration(
                main={"size": (width, height), "format": "BGR888"}
            )
            self.vid.configure(self.video_config)
            self.vid.start()
        else:
            self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        return self.get_properties()

    def get_properties(self):
        if self.is_picamera2:
            # Picamera2 retorna (width, height)
            width, height = self.vid.camera_properties['PixelArraySize']
            actual_fps = 30 # Valor típico para Raspberry Pi Camera, para consistência com o config
        else:
            width = int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.vid.get(cv2.CAP_PROP_FPS)
            if actual_fps == 0:
                actual_fps = 30 # Fallback se não conseguir ler o FPS

        return {'width': width, 'height': height, 'fps': actual_fps}

    def get_frame(self):
        if self.vid is None: 
            return (False, None)
            
        if self.is_picamera2:
            try:
                frame = self.vid.capture_array("main")
                if frame is not None:
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    return (True, frame_bgr)
            except Exception as e:
                return (False, None)
        else:
            ret, frame = self.vid.read()
            if ret:
                return (True, frame)
        
        return (False, None)

    def release(self):
        if self.vid:
            if self.is_picamera2:
                self.vid.stop()
                self.vid.close() # Liberação explícita da câmera Picamera2
            else:
                self.vid.release()
            self.vid = None # Define como None para indicar que foi liberado
            print("Recursos da câmera liberados.")