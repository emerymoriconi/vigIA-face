import tkinter as tk
from gui import GUI
from camera import Camera
from face_recognition import FaceRecognizer
from config import RESOLUTION_OPTIONS, FPS_OPTIONS
import time
import threading
import cv2
from PIL import Image, ImageTk
# Classe para controlar uma única câmera e sua GUI (como antes)
class CameraFeedController:
    def __init__(self, master, camera_index, resolution_settings, desired_fps):
        self.master = master
        self.camera_index = camera_index
        self.master.title(f"Câmera {self.camera_index} - Vídeo Feed")

        self.real_camera_fps = 30
        self.desired_fps = desired_fps # FPS desejado vindo da MainApp

        self.frame_counter = 0
        self.running = True

        try:
            self.camera = Camera(camera_index=self.camera_index)
            self.face_recognizer = FaceRecognizer()
            
            # Cria uma GUI simplificada para a janela do feed, sem os controles de seleção de câmera
            # Pois esses controles já foram definidos na MainApp.
            self.video_gui = VideoFeedGUI(master) # Usaremos uma nova classe VideoFeedGUI para as janelas de feed

            self.master.protocol("WM_DELETE_WINDOW", self.quit_app)

            actual_camera_props = self.camera.set_properties(
                width=resolution_settings['width'],
                height=resolution_settings['height'],
            )

            print(f"Câmera {self.camera_index} iniciada com resolução {resolution_settings['width']}x{resolution_settings['height']} e FPS simulado {self.desired_fps}.")
            print(f"Configurações reais da câmera {self.camera_index}: {actual_camera_props}")

            self.delay = 15
            self.update_video()

        except (ValueError, IOError) as e:
            self.show_error(str(e))

    def update_video(self):
        if not self.running:
            return

        ret, frame = self.camera.get_frame()

        if ret:
            self.frame_counter += 1

            if self.desired_fps <= 0:
                frames_per_desired_frame = 1.0
            else:
                frames_per_desired_frame = int(self.real_camera_fps / self.desired_fps)

            if self.desired_fps == self.real_camera_fps or (self.frame_counter % frames_per_desired_frame) < 1:
                processed_frame, faces_data = self.face_recognizer.process_frame(frame)
                self.video_gui.update_video_frame(processed_frame) # Atualiza a GUI do feed

        self.master.after(self.delay, self.update_video)

    def quit_app(self):
        print(f"Liberando recursos da câmera {self.camera_index} e fechando a janela do feed...")
        self.running = False
        self.camera.release()
        self.master.destroy()

    def show_error(self, message):
        error_label = tk.Label(self.master, text=message, fg="red", font=("Helvetica", 12))
        error_label.pack(pady=20, padx=20)


# Nova classe para a GUI das janelas de vídeo (simplificada, apenas o canvas)
class VideoFeedGUI:
    def __init__(self, master):
        self.master = master
        self.canvas = tk.Canvas(master, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.photo = None # Para manter a referência da imagem

    def update_video_frame(self, frame):
        h, w, _ = frame.shape
        self.canvas.config(width=w, height=h)
        
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img)
        self.photo = ImageTk.PhotoImage(image=img_pil)
        
        self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)


# Classe da aplicação principal que gerencia a GUI de controle e os controladores de câmera
class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Controle Central de Câmeras")

        self.gui = GUI(root, title="Controle Central de Câmeras")
        self.gui.set_callbacks(self.apply_settings, self.quit_app)

        self.camera_controllers = [] # Lista para manter referências a todos os controladores de câmera ativos
        self.camera_threads = [] # Lista para manter referências às threads

    def _launch_single_camera_controller(self, camera_index, resolution_settings, desired_fps):
        """Lança um CameraFeedController em uma nova janela Toplevel."""
        top_level = tk.Toplevel(self.root)
        controller = CameraFeedController(top_level, camera_index, resolution_settings, desired_fps)
        self.camera_controllers.append(controller)

    def apply_settings(self):
        """
        Callback para o botão 'Aplicar Configurações'.
        Inicia ou reinicia as câmeras com base no modo selecionado.
        """
        settings = self.gui.get_settings()
        if not settings:
            print("Nenhuma configuração válida selecionada.")
            return

        # Primeiro, fecha todas as câmeras e limpa os controladores existentes
        self._shutdown_all_cameras()

        resolution_settings = {'width': settings['width'], 'height': settings['height']}
        desired_fps = settings['desired_fps']

        if settings['mode'] == "Câmera Única":
            camera_index = settings['camera_index']
            # Lança o controlador da câmera em uma nova thread para evitar bloqueio da GUI
            thread = threading.Thread(target=self._launch_single_camera_controller, 
                                      args=(camera_index, resolution_settings, desired_fps))
            self.camera_threads.append(thread)
            thread.start()
        elif settings['mode'] == "Múltiplas Câmeras":
            # Aqui, você pode detectar automaticamente as câmeras disponíveis
            # ou usar um número fixo (ex: 0, 1, 2)
            num_detected_cameras = 2 # Exemplo: assume 2 câmeras para demonstração
            
            if desired_fps > 15:
                print(f"fps reduzido para {15} para evitar sobrecarga.")
                desired_fps = 15
            # Lógica para detectar câmeras pode ser adicionada aqui, como:
            # detected_indices = self._detect_available_cameras()
            # for idx in detected_indices:
            for idx in range(num_detected_cameras):
                thread = threading.Thread(target=self._launch_single_camera_controller, 
                                          args=(idx, resolution_settings, desired_fps))
                self.camera_threads.append(thread)
                thread.start()

        print(f"Modo '{settings['mode']}' aplicado com Resolução {settings['width']}x{settings['height']} e FPS {settings['desired_fps']}.")

    def _shutdown_all_cameras(self):
        """Desliga todos os controladores de câmera e limpa as listas."""
        for controller in self.camera_controllers:
            if controller.running:
                controller.quit_app() # Isso irá chamar master.destroy() para a janela Toplevel

        # Limpa as listas após um pequeno atraso para permitir que as threads finalizem
        self.camera_controllers = []
        self.camera_threads = []
        # Pode ser necessário um join() para as threads se a sincronização for crítica,
        # mas para este caso de encerramento, não é estritamente necessário bloquear.
        time.sleep(1) # Dá um tempo para as janelas se fecharem

    def quit_app(self):
        """Fecha a aplicação principal e todos os recursos das câmeras."""
        print("Fechando a aplicação central...")
        self._shutdown_all_cameras() # Garante que todas as câmeras sejam desligadas
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()