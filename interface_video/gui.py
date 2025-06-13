import tkinter as tk
from PIL import Image, ImageTk
import cv2

class GUI:
    def __init__(self, master, title="Interface Adaptativa para IoT"):
        self.master = master
        self.master.title(title)

       
        self.control_frame = tk.Frame(master)
        self.control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        tk.Label(self.control_frame, text="Largura:").pack(side=tk.LEFT)
        self.width_entry = tk.Entry(self.control_frame, width=7)
        self.width_entry.pack(side=tk.LEFT)

        tk.Label(self.control_frame, text="Altura:").pack(side=tk.LEFT)
        self.height_entry = tk.Entry(self.control_frame, width=7)
        self.height_entry.pack(side=tk.LEFT)

        tk.Label(self.control_frame, text="FPS:").pack(side=tk.LEFT)
        self.fps_entry = tk.Entry(self.control_frame, width=5)
        self.fps_entry.pack(side=tk.LEFT)

       
        self.apply_button = tk.Button(self.control_frame, text="Aplicar")
        self.apply_button.pack(side=tk.LEFT, padx=5)
        
       
        self.canvas = tk.Canvas(master, bg="black")
       
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def set_callbacks(self, apply_callback, quit_callback):
       
        self.apply_button.config(command=apply_callback)
        self.master.protocol("WM_DELETE_WINDOW", quit_callback) 

    def get_settings(self):
        
        try:
            return {
                'width': int(self.width_entry.get()),
                'height': int(self.height_entry.get()),
                'fps': int(self.fps_entry.get())
            }
        except ValueError:
            return None 

    def update_settings_display(self, settings):
       
        self.width_entry.delete(0, tk.END)
        self.width_entry.insert(0, str(settings['width']))
        self.height_entry.delete(0, tk.END)
        self.height_entry.insert(0, str(settings['height']))
        self.fps_entry.delete(0, tk.END)
        self.fps_entry.insert(0, str(settings['fps']))

    def update_video_frame(self, frame):
      
        h, w, _ = frame.shape
        self.canvas.config(width=w, height=h)
        
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img)
        self.photo = ImageTk.PhotoImage(image=img_pil)
        
        self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)