import tkinter as tk
from gui import GUI
from camera import Camera
from face_recognition import FaceRecognizer
from config import RESOLUTION_OPTIONS, FPS_OPTIONS

class MainController:
    def __init__(self, master):
        self.master = master

        # FPS real da câmera, que é fixo em 30 FPS (modificar na Raspberry depois)
        self.real_camera_fps = 30 

        # FPS desejado pelo usuário (para controle de descarte de frames).
        # Inicia com o primeiro FPS das opções para o menu
        self.desired_fps = FPS_OPTIONS[list(FPS_OPTIONS.keys())[0]] 

        self.frame_counter = 0
        
        try:
            self.camera = Camera()
            self.face_recognizer = FaceRecognizer()
            self.ui = GUI(master)
           
            self.ui.set_callbacks(self.apply_settings, self.quit_app)

            # Define as configurações iniciais da câmera com a primeira opção de resolução
            initial_res_settings = RESOLUTION_OPTIONS[list(RESOLUTION_OPTIONS.keys())[0]] 
            actual_camera_props = self.camera.set_properties(
                width=initial_res_settings['width'], 
                height=initial_res_settings['height'], 
            )
            
            # O FPS desejado inicial já está setado acima, baseado na primeira opção de FPS_OPTIONS

            print(f"Configurações iniciais reais da câmera: {actual_camera_props}")
            print(f"FPS inicial desejado (simulado) para exibição: {self.desired_fps}")

            self.delay = 15  
            self.update_video()
            
        except (ValueError, IOError) as e:
            self.show_error(str(e))

    def update_video(self):
        ret, frame = self.camera.get_frame()

        if ret:
            self.frame_counter += 1 

            if self.desired_fps <= 0:
                frames_per_desired_frame = 1.0 # exibe todos os frames se o desired_fps for inválido
            else:
                frames_per_desired_frame = self.real_camera_fps / self.desired_fps 
            
            # evita divisão por zero
            if self.desired_fps == self.real_camera_fps or (self.frame_counter % frames_per_desired_frame) < 1: 
                processed_frame, faces_data = self.face_recognizer.process_frame(frame)
                self.ui.update_video_frame(processed_frame)

        self.master.after(self.delay, self.update_video)

    def apply_settings(self):
        settings = self.ui.get_settings() 
        if settings:
           
            actual_camera_props = self.camera.set_properties(
                width=settings['width'], 
                height=settings['height'], 
            )
            
            # atualiza o FPS desejado para a lógica de descarte de frames
            self.desired_fps = settings['desired_fps'] 

            print(f"Configurações aplicadas: Resolução {settings['width']}x{settings['height']}, FPS simulado {self.desired_fps}")
            print(f"Configurações reais da câmera após aplicação: {actual_camera_props}")
            print(f"FPS desejado (simulado) para exibição: {self.desired_fps}")

            self.frame_counter = 0

    def quit_app(self):
        print("Liberando recursos e fechando a aplicação...")
        self.camera.release()
        self.master.destroy()

    def show_error(self, message):
        error_label = tk.Label(self.master, text=message, fg="red", font=("Helvetica", 12))
        error_label.pack(pady=20, padx=20)

if __name__ == "__main__":
    root = tk.Tk()
    app = MainController(root)
    root.mainloop()