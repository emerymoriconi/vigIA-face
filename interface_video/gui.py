import tkinter as tk
from PIL import Image, ImageTk
import cv2
from config import RESOLUTION_OPTIONS, FPS_OPTIONS

class GUI:
    def __init__(self, master, title="Interface Adaptativa para IoT"):
        self.master = master
        self.master.title(title)
       
        self.control_frame = tk.Frame(master)
        self.control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # --- Frame para o Menu de Resolução ---
        # Criamos um sub-frame para agrupar o label e o OptionMenu de Resolução
        resolution_frame = tk.Frame(self.control_frame)
        resolution_frame.pack(side=tk.TOP, pady=2, fill=tk.X) # Empacota no topo do control_frame
        tk.Label(resolution_frame, text="Tamanho da Imagem:").pack(side=tk.LEFT, padx=(0, 5))
        self.selected_resolution_name = tk.StringVar(master)
        self.selected_resolution_name.set(list(RESOLUTION_OPTIONS.keys())[0])
        self.resolution_option_menu = tk.OptionMenu(resolution_frame, self.selected_resolution_name, *list(RESOLUTION_OPTIONS.keys()))
        self.resolution_option_menu.pack(side=tk.LEFT, padx=5)

        # --- Frame para o Menu de FPS ---
        # Criamos um sub-frame para agrupar o label e o OptionMenu de FPS
        fps_frame = tk.Frame(self.control_frame)
        fps_frame.pack(side=tk.TOP, pady=2, fill=tk.X) # Empacota no topo do control_frame, logo abaixo do de resolução
        tk.Label(fps_frame, text="Fluidez do Movimento:").pack(side=tk.LEFT, padx=(0, 5)) 
        self.selected_fps_value = tk.StringVar(master)
        self.selected_fps_value.set(list(FPS_OPTIONS.keys())[0])
        self.fps_option_menu = tk.OptionMenu(fps_frame, self.selected_fps_value, *list(FPS_OPTIONS.keys()))
        self.fps_option_menu.pack(side=tk.LEFT, padx=5)
       
        self.apply_button = tk.Button(self.control_frame, text="Aplicar Configurações")
        self.apply_button.pack(side=tk.LEFT, padx=5)
       
        self.canvas = tk.Canvas(master, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def set_callbacks(self, apply_callback, quit_callback):
       
        self.apply_button.config(command=apply_callback)
        self.master.protocol("WM_DELETE_WINDOW", quit_callback) 

    def get_settings(self):
        
        # Obtém a resolução selecionada
        selected_res_name = self.selected_resolution_name.get()
        resolution_settings = RESOLUTION_OPTIONS.get(selected_res_name)

        # Obtém o FPS selecionado
        selected_fps_name = self.selected_fps_value.get()
        desired_fps = FPS_OPTIONS.get(selected_fps_name)

        # Retorna um dicionário com ambas as configurações
        if resolution_settings and desired_fps is not None:
            return {
                'width': resolution_settings['width'],
                'height': resolution_settings['height'],
                'desired_fps': desired_fps # Campo renomeado para 'desired_fps' para clareza
            }
        return None

    def update_settings_display(self, settings):
        pass

    def update_video_frame(self, frame):
      
        h, w, _ = frame.shape
        self.canvas.config(width=w, height=h)
        
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img)
        self.photo = ImageTk.PhotoImage(image=img_pil)
        
        self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)