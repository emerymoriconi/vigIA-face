import tkinter as tk
from PIL import Image, ImageTk
import cv2
from config import RESOLUTION_OPTIONS, FPS_OPTIONS

class GUI:
    def __init__(self, master, title="Interface Adaptativa para IoT"):
        self.master = master
        self.master.title(title)

        # o menu self.camera_options será preenchido dinamicamente agora
        self.camera_options = {} # { "Nome da Câmera (idx)": indice_da_camera }
        self.camera_display_names = [] # Para manter a ordem de exibição no OptionMenu

        self.control_frame = tk.Frame(master)
        self.control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # --- Frame para o Menu de Resolução ---
        resolution_frame = tk.Frame(self.control_frame)
        resolution_frame.pack(side=tk.TOP, pady=2, fill=tk.X)
        tk.Label(resolution_frame, text="Tamanho da Imagem:").pack(side=tk.LEFT, padx=(0, 5))
        self.selected_resolution_name = tk.StringVar(master)
        self.selected_resolution_name.set(list(RESOLUTION_OPTIONS.keys())[0])
        self.resolution_option_menu = tk.OptionMenu(
            resolution_frame,
            self.selected_resolution_name,
            *list(RESOLUTION_OPTIONS.keys())
        )
        self.resolution_option_menu.pack(side=tk.LEFT, padx=5)

        # --- Frame para o Menu de FPS ---
        fps_frame = tk.Frame(self.control_frame)
        fps_frame.pack(side=tk.TOP, pady=2, fill=tk.X)
        tk.Label(fps_frame, text="Fluidez do Movimento:").pack(side=tk.LEFT, padx=(0, 5))
        self.selected_fps_value = tk.StringVar(master)
        self.selected_fps_value.set(list(FPS_OPTIONS.keys())[0])
        self.fps_option_menu = tk.OptionMenu(
            fps_frame,
            self.selected_fps_value,
            *list(FPS_OPTIONS.keys())
        )
        self.fps_option_menu.pack(side=tk.LEFT, padx=5)

        # --- Frame para o Menu de Câmeras ---
        camera_frame = tk.Frame(self.control_frame)
        camera_frame.pack(side=tk.TOP, pady=2, fill=tk.X)
        tk.Label(camera_frame, text="Selecionar Câmera (Exibição):").pack(side=tk.LEFT, padx=(0, 5))
        self.selected_camera_display_name = tk.StringVar(master) # Nome para exibição
        
        # O valor inicial será definido por update_camera_options
        self.camera_option_menu = tk.OptionMenu(
            camera_frame,
            self.selected_camera_display_name,
            "Nenhuma Câmera Detectada" # Placeholder inicial
        )
        self.camera_option_menu.pack(side=tk.LEFT, padx=5)

        # --- Botão Aplicar ---
        self.apply_button = tk.Button(self.control_frame, text="Aplicar Configurações")
        self.apply_button.pack(side=tk.LEFT, padx=5)

        # --- Canvas para exibição de vídeo ---
        self.canvas = tk.Canvas(master, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.photo = None # Inicializa self.photo

    def set_callbacks(self, apply_callback, quit_callback):
        self.apply_button.config(command=apply_callback)
        self.master.protocol("WM_DELETE_WINDOW", quit_callback)

    def update_camera_options(self, camera_info_list): # Recebe uma lista de dicionários com info
        menu = self.camera_option_menu["menu"]
        menu.delete(0, "end") # Limpa as opções existentes
        
        self.camera_options = {} # Reseta o mapeamento de nome para índice
        self.camera_display_names = [] # Reseta a lista de nomes para exibição

        if not camera_info_list:
            self.selected_camera_display_name.set("Nenhuma Câmera Detectada")
            self.apply_button.config(state=tk.DISABLED) # Desabilita o botão se não houver câmeras
        else:
            for cam_info in camera_info_list:
                display_name = f"{cam_info['type']} ({cam_info['index']})"
                self.camera_options[display_name] = cam_info['index']
                self.camera_display_names.append(display_name)
            
            # Ordena os nomes para exibição no menu
            self.camera_display_names.sort()

            for name in self.camera_display_names:
                menu.add_command(label=name, command=tk._setit(self.selected_camera_display_name, name))
            
            self.selected_camera_display_name.set(self.camera_display_names[0]) # Seleciona a primeira câmera por padrão
            self.apply_button.config(state=tk.NORMAL) # Habilita o botão

    def get_settings(self):
        selected_res_name = self.selected_resolution_name.get()
        resolution_settings = RESOLUTION_OPTIONS.get(selected_res_name)

        selected_fps_name = self.selected_fps_value.get()
        desired_fps = FPS_OPTIONS.get(selected_fps_name)

        # Obtém o índice da câmera selecionada para exibição
        selected_display_name = self.selected_camera_display_name.get()
        camera_num_to_display = self.camera_options.get(selected_display_name, None)

        if resolution_settings and desired_fps is not None and camera_num_to_display is not None:
            return {
                'width': resolution_settings['width'],
                'height': resolution_settings['height'],
                'desired_fps': desired_fps,
                'camera_num_to_display': camera_num_to_display # Indica qual câmera exibir
            }
        return None

    def update_video_frame(self, frame):
        if frame is None:
            # Desenha um retângulo preto no canvas se não houver frame válido
            self.canvas.delete("all")
            self.canvas.config(bg="black")
            return

        h, w, _ = frame.shape
        # Redimensiona o canvas apenas se a resolução do frame mudar, para evitar piscar.
        if self.canvas.winfo_width() != w or self.canvas.winfo_height() != h:
            self.canvas.config(width=w, height=h)

        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img)
        self.photo = ImageTk.PhotoImage(image=img_pil)

        self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)