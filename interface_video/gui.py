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

        # --- Frame para o Menu de Modo de Câmera ---
        mode_frame = tk.Frame(self.control_frame)
        mode_frame.pack(side=tk.TOP, pady=2, fill=tk.X)
        tk.Label(mode_frame, text="Modo de Câmera:").pack(side=tk.LEFT, padx=(0, 5))
        self.selected_camera_mode = tk.StringVar(master)
        self.selected_camera_mode.set("Câmera Única")  # Valor padrão
        self.camera_mode_option_menu = tk.OptionMenu(mode_frame, self.selected_camera_mode, "Câmera Única", "Múltiplas Câmeras")
        self.camera_mode_option_menu.pack(side=tk.LEFT, padx=5)
        self.selected_camera_mode.trace("w", self._on_camera_mode_change) # Adiciona rastreador de mudança

        # --- Frame para o Menu de Câmeras (seleção individual) ---
        self.camera_selection_frame = tk.Frame(self.control_frame)
        self.camera_selection_frame.pack(side=tk.TOP, pady=2, fill=tk.X)
        tk.Label(self.camera_selection_frame, text="Selecionar Câmera:").pack(side=tk.LEFT, padx=(0, 5))
        self.selected_camera_index = tk.StringVar(master)
        self.selected_camera_index.set("0")  # valor padrão
        self.camera_option_menu = tk.OptionMenu(self.camera_selection_frame, self.selected_camera_index, *[str(i) for i in range(4)])
        self.camera_option_menu.pack(side=tk.LEFT, padx=5)

        # --- Frame para o Menu de Resolução ---
        resolution_frame = tk.Frame(self.control_frame)
        resolution_frame.pack(side=tk.TOP, pady=2, fill=tk.X)
        tk.Label(resolution_frame, text="Tamanho da Imagem:").pack(side=tk.LEFT, padx=(0, 5))
        self.selected_resolution_name = tk.StringVar(master)
        self.selected_resolution_name.set(list(RESOLUTION_OPTIONS.keys())[0])
        self.resolution_option_menu = tk.OptionMenu(resolution_frame, self.selected_resolution_name, *list(RESOLUTION_OPTIONS.keys()))
        self.resolution_option_menu.pack(side=tk.LEFT, padx=5)

        # --- Frame para o Menu de FPS ---
        fps_frame = tk.Frame(self.control_frame)
        fps_frame.pack(side=tk.TOP, pady=2, fill=tk.X)
        tk.Label(fps_frame, text="Fluidez do Movimento:").pack(side=tk.LEFT, padx=(0, 5)) 
        self.selected_fps_value = tk.StringVar(master)
        self.selected_fps_value.set(list(FPS_OPTIONS.keys())[0])
        self.fps_option_menu = tk.OptionMenu(fps_frame, self.selected_fps_value, *list(FPS_OPTIONS.keys()))
        self.fps_option_menu.pack(side=tk.LEFT, padx=5)
       
        self.apply_button = tk.Button(self.control_frame, text="Aplicar Configurações")
        self.apply_button.pack(side=tk.LEFT, padx=5)
       
        # Canvas para exibir o vídeo (inicialmente apenas para uma câmera, adaptaremos para múltiplas janelas)
        self.canvas_placeholder = tk.Label(master, text="Clique em 'Aplicar Configurações' para iniciar a(s) câmera(s).")
        self.canvas_placeholder.pack(fill=tk.BOTH, expand=True)
        self.current_photo = None # Para manter a referência da imagem PIL/Tkinter

    def _on_camera_mode_change(self, *args):
        """Habilita/desabilita o seletor de câmera com base no modo selecionado."""
        if self.selected_camera_mode.get() == "Câmera Única":
            self.camera_selection_frame.pack(side=tk.TOP, pady=2, fill=tk.X)
            for child in self.camera_selection_frame.winfo_children():
                child.config(state=tk.NORMAL)
        else:
            self.camera_selection_frame.pack_forget() # Oculta o frame de seleção de câmera
            # Ou, se preferir desabilitar em vez de ocultar:
            # for child in self.camera_selection_frame.winfo_children():
            #     child.config(state=tk.DISABLED)

    def set_callbacks(self, apply_callback, quit_callback):
        self.apply_button.config(command=apply_callback)
        self.master.protocol("WM_DELETE_WINDOW", quit_callback)

    def get_settings(self):
        """Retorna as configurações selecionadas pelo usuário."""
        mode = self.selected_camera_mode.get()
        camera_index = None
        if mode == "Câmera Única":
            camera_index = int(self.selected_camera_index.get())
        
        selected_res_name = self.selected_resolution_name.get()
        resolution_settings = RESOLUTION_OPTIONS.get(selected_res_name)

        selected_fps_name = self.selected_fps_value.get()
        desired_fps = FPS_OPTIONS.get(selected_fps_name)

        if resolution_settings and desired_fps is not None:
            return {
                'mode': mode,
                'camera_index': camera_index, # Será None se for Múltiplas Câmeras
                'width': resolution_settings['width'],
                'height': resolution_settings['height'],
                'desired_fps': desired_fps,
            }
        return None

    def update_video_frame(self, frame):
        """
        Atualiza o frame de vídeo no canvas.
        Nota: Esta GUI principal agora é apenas um placeholder para a interface de controle.
        As janelas de vídeo reais serão criadas separadamente.
        """
        if self.canvas_placeholder:
            self.canvas_placeholder.destroy() # Remove o placeholder quando o vídeo começa a ser exibido

        # Para compatibilidade, manter um canvas se esta GUI principal precisar exibir algo.
        # No entanto, na solução de múltiplas câmeras, cada câmera terá sua própria GUI/janela.
        # Esta função pode não ser mais chamada pela lógica do CameraFeedController em main.py
        # se as câmeras forem lançadas em Toplevels separados.
        # Se for para esta GUI principal exibir algo, ela precisaria de um canvas para si.
        # No nosso caso, esta GUI é apenas para controle e lançamento.

        # A lógica abaixo é para o caso de uma única câmera (se o apply_settings decidisse usar este canvas)
        # Se a arquitetura mudar para múltiplos Toplevels, esta parte pode ser removida ou adaptada.
        h, w, _ = frame.shape
        # Se esta GUI tiver seu próprio canvas (por exemplo, self.canvas = tk.Canvas(...))
        # self.canvas.config(width=w, height=h)
        # img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # img_pil = Image.fromarray(img)
        # self.current_photo = ImageTk.PhotoImage(image=img_pil) # Atualizado para self.current_photo
        # self.canvas.create_image(0, 0, image=self.current_photo, anchor=tk.NW)
        pass # Não faz nada no canvas principal, pois as câmeras terão suas próprias janelas.