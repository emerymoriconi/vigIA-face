import tkinter as tk
from PIL import Image, ImageTk
import cv2
from config import RESOLUTION_OPTIONS, FPS_OPTIONS

class GUI:
    def __init__(self, master, available_cameras, title="Interface Adaptativa para IoT"):
        """
        Args:
            available_cameras: Lista de dicts com {index, name, type, use_opencv}
        """
        self.master = master
        self.master.title(title)
        self.available_cameras = available_cameras
       
        self.control_frame = tk.Frame(master)
        self.control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # --- Modo de Câmera ---
        mode_frame = tk.Frame(self.control_frame)
        mode_frame.pack(side=tk.TOP, pady=2, fill=tk.X)
        tk.Label(mode_frame, text="Modo de Câmera:").pack(side=tk.LEFT, padx=(0, 5))
        self.selected_camera_mode = tk.StringVar(master)
        self.selected_camera_mode.set("Câmera Única")
        self.camera_mode_option_menu = tk.OptionMenu(
            mode_frame, self.selected_camera_mode, 
            "Câmera Única", "Múltiplas Câmeras"
        )
        self.camera_mode_option_menu.pack(side=tk.LEFT, padx=5)
        self.selected_camera_mode.trace("w", self._on_camera_mode_change)

        # --- MODO DE PROCESSAMENTO (NOVO) ---
        processing_frame = tk.Frame(self.control_frame)
        processing_frame.pack(side=tk.TOP, pady=2, fill=tk.X)
        tk.Label(processing_frame, text="Modo de Processamento:").pack(side=tk.LEFT, padx=(0, 5))
        self.selected_processing_mode = tk.StringVar(master)
        
        # Define as opções de processamento
        self.processing_options = {
            "Local (Apenas Detecção)": "local",
            "Cenário 1 (Detec. Local)": "scenario_1",
            "Cenário 2 (Sem Detec. Local)": "scenario_2",
            "Cenário 3 (Detec. Local/Vetor)": "scenario_3",
            # "Cenário 2 (API - Central)": "scenario_2" # Descomente quando estiver pronto
        }
        
        # Define o padrão para o Cenário 3
        self.selected_processing_mode.set("Cenário 3 (Detec. Local/Vetor)") 
        
        self.processing_option_menu = tk.OptionMenu(
            processing_frame,
            self.selected_processing_mode,
            *list(self.processing_options.keys())
        )
        self.processing_option_menu.pack(side=tk.LEFT, padx=5)
        # --- FIM DO NOVO BLOCO ---

        # --- Seleção de Câmera Individual ---
        self.camera_selection_frame = tk.Frame(self.control_frame)
        self.camera_selection_frame.pack(side=tk.TOP, pady=2, fill=tk.X)
        tk.Label(self.camera_selection_frame, text="Selecionar Câmera:").pack(side=tk.LEFT, padx=(0, 5))
        self.selected_camera_index = tk.StringVar(master)
        
        # Cria menu com nomes das câmeras
        if available_cameras:
            camera_options = [f"[{c['index']}] {c['type']}: {c['name']}" for c in available_cameras]
            self.selected_camera_index.set(camera_options[0])
            self.camera_option_menu = tk.OptionMenu(
                self.camera_selection_frame, 
                self.selected_camera_index, 
                *camera_options
            )
        else:
            self.selected_camera_index.set("Nenhuma câmera detectada")
            self.camera_option_menu = tk.OptionMenu(
                self.camera_selection_frame, 
                self.selected_camera_index, 
                "Nenhuma câmera detectada"
            )
            self.camera_option_menu.config(state=tk.DISABLED)
        
        self.camera_option_menu.pack(side=tk.LEFT, padx=5)

        # --- Resolução ---
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

        # --- FPS ---
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
       
        # --- Botão Aplicar ---
        self.apply_button = tk.Button(self.control_frame, text="Aplicar Configurações")
        self.apply_button.pack(side=tk.LEFT, padx=5)
        if not available_cameras:
            self.apply_button.config(state=tk.DISABLED)
       
        # --- Placeholder ---
        self.canvas_placeholder = tk.Label(
            master, 
            text="Clique em 'Aplicar Configurações' para iniciar a(s) câmera(s)."
        )
        if not available_cameras:
            self.canvas_placeholder.config(text="Nenhuma câmera detectada.")
        self.canvas_placeholder.pack(fill=tk.BOTH, expand=True)
        self.current_photo = None

    def _on_camera_mode_change(self, *args):
        if self.selected_camera_mode.get() == "Câmera Única":
            self.camera_selection_frame.pack(side=tk.TOP, pady=2, fill=tk.X)
        else:
            self.camera_selection_frame.pack_forget()

    def set_callbacks(self, apply_callback, quit_callback):
        self.apply_button.config(command=apply_callback)
        self.master.protocol("WM_DELETE_WINDOW", quit_callback)

    def get_settings(self):
        """Retorna settings com índice, use_opencv e modo de processamento corretos"""
        mode = self.selected_camera_mode.get()
        camera_info = None
        
        if mode == "Câmera Única":
            # Extrai índice da string "[0] CSI: ov5647"
            selected_text = self.selected_camera_index.get()
            if selected_text != "Nenhuma câmera detectada":
                try:
                    index = int(selected_text.split(']')[0].split('[')[1])
                    # Encontra info completa da câmera
                    for cam in self.available_cameras:
                        if cam['index'] == index:
                            camera_info = cam
                            break
                except:
                    return None
        
        resolution_settings = RESOLUTION_OPTIONS.get(self.selected_resolution_name.get())
        desired_fps = FPS_OPTIONS.get(self.selected_fps_value.get())

       
        processing_mode_key = self.selected_processing_mode.get()
        processing_mode_value = self.processing_options.get(processing_mode_key, "local")


        if resolution_settings and desired_fps is not None:
            return {
                'mode': mode,
                'camera_info': camera_info,  # Passa dict completo
                'width': resolution_settings['width'],
                'height': resolution_settings['height'],
                'desired_fps': desired_fps,
                'processing_mode': processing_mode_value  # <--- RETORNA O MODO ESCOLHIDO
            }
        return None