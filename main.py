# main.py

import tkinter as tk
import cv2
from PIL import Image, ImageTk # Usaremos PIL para converter imagens do OpenCV para Tkinter

class VideoApp:
    def __init__(self, window, window_title="Interface Adaptativa"):
        self.window = window
        self.window.title(window_title)

        # Configurações iniciais da câmera
        self.vid = cv2.VideoCapture(0, cv2.CAP_DSHOW) # '0' para a câmera padrão
        if not self.vid.isOpened():
            raise ValueError("Não foi possível abrir a câmera. Verifique se ela está conectada e disponível.")

        # Obtendo as configurações atuais da câmera
        self.current_width = int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.current_height = int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.current_fps = int(self.vid.get(cv2.CAP_PROP_FPS))
        if self.current_fps == 0: # Algumas câmeras podem retornar 0 FPS, definimos um padrão
            self.current_fps = 30

        # Frame para os controles de vídeo
        self.control_frame = tk.Frame(window)
        self.control_frame.pack(side=tk.TOP, pady=10)

        # Labels e Entradas para Largura, Altura e FPS
        tk.Label(self.control_frame, text="Largura:").pack(side=tk.LEFT, padx=5)
        self.width_entry = tk.Entry(self.control_frame, width=10)
        self.width_entry.insert(0, str(self.current_width))
        self.width_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(self.control_frame, text="Altura:").pack(side=tk.LEFT, padx=5)
        self.height_entry = tk.Entry(self.control_frame, width=10)
        self.height_entry.insert(0, str(self.current_height))
        self.height_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(self.control_frame, text="FPS:").pack(side=tk.LEFT, padx=5)
        self.fps_entry = tk.Entry(self.control_frame, width=10)
        self.fps_entry.insert(0, str(self.current_fps))
        self.fps_entry.pack(side=tk.LEFT, padx=5)

        # Botão para aplicar as configurações
        self.apply_button = tk.Button(self.control_frame, text="Aplicar Configurações", command=self.apply_settings)
        self.apply_button.pack(side=tk.LEFT, padx=10)

        # Canvas para exibir o vídeo
        self.canvas = tk.Canvas(window, width=self.current_width, height=self.current_height)
        self.canvas.pack()

        # Botão para sair
        self.btn_quit = tk.Button(window, text="Sair", command=self.quit_app)
        self.btn_quit.pack(pady=10)

        # Loop para atualizar o vídeo
        self.delay = 15 # milliseconds
        self.update()

        self.window.mainloop()

    def apply_settings(self):
        try:
            new_width = int(self.width_entry.get())
            new_height = int(self.height_entry.get())
            new_fps = int(self.fps_entry.get())

            # Tenta aplicar as novas configurações
            self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, new_width)
            self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, new_height)
            self.vid.set(cv2.CAP_PROP_FPS, new_fps)

            # Atualiza as variáveis internas com os valores que a câmera realmente conseguiu configurar
            self.current_width = int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.current_height = int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.current_fps = int(self.vid.get(cv2.CAP_PROP_FPS))

            # Atualiza o tamanho do canvas
            self.canvas.config(width=self.current_width, height=self.current_height)

            # Opcional: Atualizar as caixas de texto com os valores reais após a configuração
            self.width_entry.delete(0, tk.END)
            self.width_entry.insert(0, str(self.current_width))
            self.height_entry.delete(0, tk.END)
            self.height_entry.insert(0, str(self.current_height))
            self.fps_entry.delete(0, tk.END)
            self.fps_entry.insert(0, str(self.current_fps))

            print(f"Configurações aplicadas: Largura={self.current_width}, Altura={self.current_height}, FPS={self.current_fps}")

        except ValueError:
            print("Por favor, insira números inteiros válidos para Largura, Altura e FPS.")

    def update(self):
        # Captura o frame da câmera
        ret, frame = self.vid.read()

        if ret:
            # Converte o frame do OpenCV (BGR) para RGB
            self.image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Converte para um objeto ImageTk (compatível com Tkinter)
            self.image = Image.fromarray(self.image)
            self.photo = ImageTk.PhotoImage(image=self.image)

            # Exibe a imagem no canvas
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        else:
            print("Não foi possível ler o frame da câmera.")

        # Chama a função 'update' novamente após um atraso (para criar o loop de vídeo)
        self.window.after(self.delay, self.update)

    def quit_app(self):
        self.vid.release() # Libera a câmera
        self.window.destroy() # Fecha a janela Tkinter

# Cria a janela principal e inicia a aplicação
if __name__ == "__main__":
    root = tk.Tk()
    app = VideoApp(root)