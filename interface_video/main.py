import tkinter as tk
from gui import GUI
from camera import Camera
from face_recognition import FaceRecognizer

class MainController:
    def __init__(self, master):
        self.master = master
        try:
          
            self.camera = Camera(0)
            self.face_recognizer = FaceRecognizer()
            self.ui = GUI(master)

           
            self.ui.set_callbacks(self.apply_settings, self.quit_app)

            initial_settings = self.camera.get_properties()
            self.ui.update_settings_display(initial_settings)
            
            self.delay = 15  
            self.update_video()
            
        except (ValueError, IOError) as e:

            self.show_error(str(e))

    def update_video(self):
        
        ret, frame = self.camera.get_frame()

        if ret:
            processed_frame, faces_data = self.face_recognizer.process_frame(frame)

            self.ui.update_video_frame(processed_frame)

        self.master.after(self.delay, self.update_video)

    def apply_settings(self):
        settings = self.ui.get_settings()
        if settings:
            print(f"Aplicando novas configurações: {settings}")
            actual_settings = self.camera.set_properties(**settings)
            self.ui.update_settings_display(actual_settings)
            print(f"Configurações reais aplicadas: {actual_settings}")

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