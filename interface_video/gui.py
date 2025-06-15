import tkinter as tk
from PIL import Image, ImageTk
import cv2
from config import RESOLUTIONS

class GUI:
    def __init__(self, master, title="Interface Adaptativa para IoT"):
        self.master = master
        self.master.title(title)
       
        self.control_frame = tk.Frame(master)
        self.control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # variável Tkinter para armazenar a seleção do menu
        self.selected_resolution_name = tk.StringVar(master)
        # opção padrão 
        self.selected_resolution_name.set("Qualidade Padrão (360p 16:9)") 

        # menu suspenso para seleção da resolução
        self.resolution_option_menu = tk.OptionMenu(self.control_frame, self.selected_resolution_name, *list(RESOLUTIONS.keys())) 
        self.resolution_option_menu.pack(side=tk.LEFT, padx=5)
       
        self.apply_button = tk.Button(self.control_frame, text="Aplicar")
        self.apply_button.pack(side=tk.LEFT, padx=5)
       
        self.canvas = tk.Canvas(master, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def set_callbacks(self, apply_callback, quit_callback):
       
        self.apply_button.config(command=apply_callback)
        self.master.protocol("WM_DELETE_WINDOW", quit_callback) 

    def get_settings(self):
        
        selected_name = self.selected_resolution_name.get() # obtém o nome da resolução selecionada no menu
        return RESOLUTIONS.get(selected_name)

    def update_settings_display(self, settings):
        pass

    def update_video_frame(self, frame):
      
        h, w, _ = frame.shape
        self.canvas.config(width=w, height=h)
        
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img)
        self.photo = ImageTk.PhotoImage(image=img_pil)
        
        self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)