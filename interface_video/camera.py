
from picamera2 import Picamera2


class Camera:
   
    def __init__(self):
        # Inicializa a câmera usando picamera2
        self.vid = Picamera2()
        
        # Configurações padrão para a pré-visualização e captura.
        # Define o stream principal com uma resolução inicial e formato BGR888 para compatibilidade com OpenCV.
        # Um stream 'lores' (baixa resolução) pode ser adicionado se você quiser uma pré-visualização separada,
        # mas para sua aplicação, o stream 'main' será exibido diretamente.
        self.video_config = self.vid.create_video_configuration(main={"size": (640, 480), "format": "BGR888"}) 
        self.vid.configure(self.video_config)
        self.vid.start()
        
        print(f"Câmera inicializada com picamera2.")

    def set_properties(self, width, height):
        # Interrompe a câmera para aplicar novas configurações
        self.vid.stop() 
        
        # Cria uma nova configuração de vídeo com a resolução desejada.
        # O FPS não é diretamente "setado" aqui como em cv2.VideoCapture.
        # O picamera2 tentará a taxa de quadros máxima para a resolução especificada,
        # que geralmente será 30 FPS para as resoluções que você listou.
        self.video_config = self.vid.create_video_configuration(main={"size": (width, height), "format": "BGR888"})
        self.vid.configure(self.video_config)
        self.vid.start()
        
        # Retorna as propriedades que foram definidas (ou as mais próximas que a câmera pode suportar).
        return self.get_properties()

    def get_properties(self):
        # Obtém a resolução atual do stream 'main' após a configuração.
        width, height = self.vid.camera_properties['PixelArraySize'] 
        
        # Para o FPS, a picamera2 não expõe um CAP_PROP_FPS fácil para o FPS real durante o streaming.
        # Considerando que a Raspberry Pi Camera V2 geralmente opera a 30 FPS para essas resoluções,
        # vamos retornar 30 como o FPS "real" que o programa usará para a lógica de descarte.
        # Isso pode ser ajustado se você tiver uma câmera com capacidades diferentes.
        actual_fps = 30 # Valor típico para a Raspberry Pi Camera V2
        return {'width': width, 'height': height, 'fps': actual_fps}

    def get_frame(self):
        # Captura um frame do stream principal como um array NumPy.
        # 'copy=False' pode ser usado para evitar a cópia, mas 'capture_array' já retorna uma cópia para segurança.
        frame = self.vid.capture_array("main")
        if frame is not None:
            return (True, frame)
        return (False, None)

    def release(self):
        # Para a câmera e libera os recursos
        self.vid.stop()
        print("Recursos da câmera liberados.")