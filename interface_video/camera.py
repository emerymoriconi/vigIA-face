import cv2
from picamera2 import Picamera2

class Camera:
    def __init__(self, camera_num=0):
        # Inicializa a câmera com o número especificado
        self.vid = Picamera2(camera_num=camera_num)

        # Configuração padrão de vídeo (resolução inicial)
        self.video_config = self.vid.create_video_configuration(
            main={"size": (640, 480), "format": "BGR888"}
        )
        self.vid.configure(self.video_config)
        self.vid.start()

        print(f"Câmera {camera_num} inicializada com Picamera2.")

    def set_properties(self, width, height):
        self.vid.stop()

        self.video_config = self.vid.create_video_configuration(
            main={"size": (width, height), "format": "BGR888"}
        )
        self.vid.configure(self.video_config)
        self.vid.start()

        return self.get_properties()

    def get_properties(self):
        width, height = self.vid.camera_properties['PixelArraySize']

        actual_fps = 30  # Valor típico para Raspberry Pi Camera
        return {'width': width, 'height': height, 'fps': actual_fps}

    def get_frame(self):
        frame = self.vid.capture_array("main")
        if frame is not None:
            print("Frame capturado")
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            return (True, frame_bgr)

        print("Falha ao capturar frame")
        return (False, None)

    def release(self):
        self.vid.stop()
        print("Recursos da câmera liberados.")
