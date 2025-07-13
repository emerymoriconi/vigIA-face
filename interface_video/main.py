import tkinter as tk
import threading
import time
import cv2 # Para detectar câmeras USB
import queue # Para filas thread-safe

from gui import GUI
from camera import Camera
from face_recognition import FaceRecognizer
from config import RESOLUTION_OPTIONS, FPS_OPTIONS

# CameraWorker para rodar a câmera em uma thread separada
class CameraWorker(threading.Thread):
    def __init__(self, camera_instance, face_recognizer, frame_queue, desired_fps, camera_num): # Recebe uma fila
        super().__init__()
        self.camera = camera_instance
        self.face_recognizer = face_recognizer
        self.frame_queue = frame_queue # Fila para enviar frames para a GUI
        self.desired_fps = desired_fps
        self.camera_num = camera_num
        self.running = True
        self.frame_counter = 0

    def run(self):
        real_camera_fps = self.camera.get_properties().get('fps', 30)
        print(f"CameraWorker da Câmera {self.camera_num} (ID Thread: {self.native_id}) iniciado. FPS real: {real_camera_fps}, FPS desejado: {self.desired_fps}")

        while self.running:
            ret, frame = self.camera.get_frame()

            if ret:
                self.frame_counter += 1

                if self.desired_fps <= 0:
                    frames_to_skip = 0
                else:
                    frames_to_skip = max(0, int(real_camera_fps / self.desired_fps) - 1)

                if (self.frame_counter % (frames_to_skip + 1)) == 0:
                    processed_frame, _ = self.face_recognizer.process_frame(frame)
                    
                    # Coloca o frame processado na fila
                    try:
                        # Usamos put_nowait para evitar bloqueio caso a fila esteja cheia,
                        # descartando frames se a GUI não conseguir acompanhar
                        self.frame_queue.put_nowait(processed_frame) 
                    except queue.Full:
                        pass # Apenas descarta o frame se a fila estiver cheia

            if real_camera_fps > 0:
                 time.sleep(1 / real_camera_fps)
            else:
                time.sleep(0.033) # Aproximadamente 30 FPS


    def stop(self):
        self.running = False
        print(f"Sinal para parar CameraWorker da câmera {self.camera_num} (ID Thread: {self.native_id}) enviado.")


class MainController:
    def __init__(self, master):
        self.master = master
        self.face_recognizer = FaceRecognizer()
        self.ui = GUI(master)
        self.ui.set_callbacks(self.apply_settings, self.quit_app)

        self.camera_workers = {} # Dicionário para armazenar todas as threads de câmera ativas {camera_num: CameraWorker}
        self.camera_frame_queues = {} # Dicionário de filas de frames por câmera {camera_num: queue.Queue}
        self.available_cameras_info = [] # Lista de dicionários com info das câmeras detectadas

        self.camera_exibicao_atual_index = None # Qual câmera está sendo exibida no momento
        self.delay = 15 # Atraso para o loop principal da GUI (tkinter.after)

        self.initialize_application()

    def initialize_application(self):
        try:
            self.detect_and_populate_camera_options() # Detecção e preenchimento da GUI
            
            if not self.available_cameras_info:
                self.show_error("Nenhuma câmera detectada. Verifique as conexões.")
                return

            # Inicia CameraWorkers para TODAS as câmeras detectadas
            for cam_info in self.available_cameras_info:
                initial_resolution = RESOLUTION_OPTIONS[list(RESOLUTION_OPTIONS.keys())[0]]
                initial_desired_fps = FPS_OPTIONS[list(FPS_OPTIONS.keys())[0]]
                self.start_camera_worker(
                    cam_info['index'],
                    initial_resolution['width'],
                    initial_resolution['height'],
                    initial_desired_fps # Pode ser o FPS máximo ou um valor padrão para todas as threads
                )
            
            # Define qual câmera será exibida inicialmente
            # Prioriza a câmera 0, se ativa. Caso contrário, a próxima ativa.
            self.camera_exibicao_atual_index = self.get_prioritized_display_camera_index()
            print(f"Câmera inicial para exibição: {self.camera_exibicao_atual_index}")

            # Loop principal da GUI para atualização de vídeo (puxa frames das filas)
            self.master.after(self.delay, self.update_gui_loop)

        except (ValueError, IOError) as e:
            self.show_error(str(e))

    def detect_and_populate_camera_options(self):
        self.available_cameras_info = []
        camera_options_for_gui = {}

        # Tenta detectar câmeras Picamera2 (Raspberry Pi Camera Module)
        try:
            temp_picam = Picamera2(0) # Tenta abrir a câmera Picamera2 no índice 0
            temp_picam.start()
            test_picam_props = temp_picam.camera_properties
            temp_picam.stop()
            temp_picam.close() # Libera o recurso explicitamente

            self.available_cameras_info.append({
                "index": 0,
                "type": "Raspberry Pi Camera",
                "width": test_picam_props['PixelArraySize'][0],
                "height": test_picam_props['PixelArraySize'][1]
            })
            camera_options_for_gui["Câmera Raspberry Pi (0)"] = 0
            print("Raspberry Pi Camera (0) detectada.")
        except Exception as e:
            print(f"Não foi possível detectar Raspberry Pi Camera (0): {e}")

        # Tenta detectar webcams USB com OpenCV
        for i in range(10): 
            if i == 0 and any(c['type'] == "Raspberry Pi Camera" for c in self.available_cameras_info):
                continue # Já lidamos com a Picamera2 no índice 0
            
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                backend_name = cap.getBackendName()
                cap.release()

                cam_type_name = "Webcam USB"
                self.available_cameras_info.append({
                    "index": i,
                    "type": cam_type_name,
                    "width": width,
                    "height": height
                })
                camera_options_for_gui[f"{cam_type_name} ({i})"] = i
                print(f"{cam_type_name} ({i}) detectada com {backend_name}.")
            else:
                cap.release()

        self.ui.update_camera_options(self.available_cameras_info) # Passa a lista de info
        if not self.available_cameras_info:
            print("Nenhuma câmera detectada no sistema.")
        else:
            print(f"Câmeras detectadas: {[c['index'] for c in self.available_cameras_info]}")

    # Para iniciar UM CameraWorker (todas rodarão em paralelo)
    def start_camera_worker(self, camera_num, width, height, desired_fps):
        if camera_num in self.camera_workers and self.camera_workers[camera_num].is_alive():
            print(f"Câmera {camera_num} já está ativa. Parando e reiniciando com novas configs.")
            self.stop_camera_worker(camera_num)

        try:
            camera_instance = Camera(camera_num=camera_num)
            camera_instance.set_properties(width, height) 

            # Cria uma fila específica para esta câmera
            # A fila tem um tamanho máximo para evitar que a memória exploda se a GUI for lenta.
            self.camera_frame_queues[camera_num] = queue.Queue(maxsize=5) 

            worker = CameraWorker(
                camera_instance,
                self.face_recognizer,
                self.camera_frame_queues[camera_num], # Passa a fila para o worker
                desired_fps,
                camera_num
            )
            worker.daemon = True # Permite que o programa principal saia mesmo se a thread estiver rodando
            worker.start()
            self.camera_workers[camera_num] = worker # Adiciona o worker ao dicionário de workers ativos
            print(f"CameraWorker para a câmera {camera_num} iniciado com resolução {width}x{height}, FPS desejado {desired_fps}.")

        except (ValueError, IOError) as e:
            self.show_error(f"Erro ao iniciar a câmera {camera_num}: {str(e)}")
            if camera_num in self.camera_workers:
                del self.camera_workers[camera_num] # Remove o worker que falhou
            if camera_num in self.camera_frame_queues:
                del self.camera_frame_queues[camera_num]

    # Para parar UM CameraWorker específico
    def stop_camera_worker(self, camera_num):
        if camera_num in self.camera_workers and self.camera_workers[camera_num].is_alive():
            worker = self.camera_workers[camera_num]
            worker.stop()
            worker.join(timeout=2) # Espera um pouco para a thread terminar
            if worker.is_alive():
                print(f"Aviso: CameraWorker da câmera {camera_num} não encerrou completamente.")
            del self.camera_workers[camera_num]
            # Limpa a fila também
            if camera_num in self.camera_frame_queues:
                with self.camera_frame_queues[camera_num].mutex:
                    self.camera_frame_queues[camera_num].queue.clear()
                del self.camera_frame_queues[camera_num]
            print(f"CameraWorker para a câmera {camera_num} parado e recursos liberados.")

    # Prioriza qual câmera exibir
    def get_prioritized_display_camera_index(self):
        # Tenta a câmera 0 primeiro
        if 0 in self.camera_workers and self.camera_workers[0].is_alive():
            return 0
        
        # Se a câmera 0 não está ativa, procura a próxima câmera ativa na lista
        for cam_info in self.available_cameras_info:
            if cam_info['index'] in self.camera_workers and self.camera_workers[cam_info['index']].is_alive():
                return cam_info['index']
        
        return None # Nenhuma câmera ativa para exibir

    # Loop principal da GUI agora exibe o frame da câmera atual
    def update_gui_loop(self):
        frame_to_display = None
    
        # Verifica se a câmera atualmente selecionada para exibição ainda está ativa
        if self.camera_exibicao_atual_index is not None and \
           self.camera_exibicao_atual_index in self.camera_workers and \
           self.camera_workers[self.camera_exibicao_atual_index].is_alive():
            
            current_camera_queue = self.camera_frame_queues.get(self.camera_exibicao_atual_index)
            if current_camera_queue:
                try:
                    frame_to_display = current_camera_queue.get_nowait() # Tenta pegar um frame sem bloquear
                except queue.Empty:
                    # Nenhuma frame novo na fila da câmera atual, usa o último frame exibido ou um frame em branco
                    pass # Deixa frame_to_display como None se não tiver nada novo
        
        # Se a câmera de exibição atual não está ativa ou não tem frames,
        # tenta encontrar uma câmera ativa para exibir (prioridade da lista)
        if frame_to_display is None:
            # Encontra a próxima câmera ativa na lista de prioridade
            next_display_index = self.get_prioritized_display_camera_index()
            
            if next_display_index is not None and next_display_index != self.camera_exibicao_atual_index:
                print(f"Câmera de exibição {self.camera_exibicao_atual_index} inativa ou sem frames. Mudando para {next_display_index}.")
                self.camera_exibicao_atual_index = next_display_index
                # Tenta pegar um frame da nova câmera de exibição
                next_camera_queue = self.camera_frame_queues.get(self.camera_exibicao_atual_index)
                if next_camera_queue:
                    try:
                        frame_to_display = next_camera_queue.get_nowait()
                    except queue.Empty:
                        pass # Continua como None se a próxima câmera também não tiver frame imediato

        # Atualiza a GUI com o frame (pode ser None se nenhuma câmera ativa tiver frames ou se não houver câmeras)
        self.ui.update_video_frame(frame_to_display)
        
        # Agenda a próxima atualização
        self.master.after(self.delay, self.update_gui_loop)


    def apply_settings(self):
        settings = self.ui.get_settings()
        if not settings:
            self.show_error("Configurações inválidas ou nenhuma câmera selecionada.")
            return

        # O FPS desejado se aplica a todas as threads ativas
        new_desired_fps = settings['desired_fps']
        # camera_num_to_display é a Câmera que o usuário escolheu para EXIBIR
        camera_num_to_display_selected_by_user = settings['camera_num_to_display']
        
        # Verifica se as configurações de FPS mudaram para cada worker
        for cam_idx, worker in self.camera_workers.items():
            if worker.desired_fps != new_desired_fps:
                print(f"Atualizando FPS desejado para Câmera {cam_idx} de {worker.desired_fps} para {new_desired_fps}")
                # Reinicia a thread com o novo FPS desejado (mantendo resolução atual)
                current_cam_props = worker.camera.get_properties()
                self.stop_camera_worker(cam_idx)
                self.start_camera_worker(
                    cam_idx,
                    current_cam_props['width'],
                    current_cam_props['height'],
                    new_desired_fps
                )
            
            # O problema da alternância de resolução pode ser resolvido também
            # mudando a resolução de TODAS as câmeras ativas.
            # Se a resolução selecionada na GUI for diferente da que a câmera está usando,
            # reinicia a thread para aplicar a nova resolução.
            if worker.camera.get_properties()['width'] != settings['width'] or \
               worker.camera.get_properties()['height'] != settings['height']:
                print(f"Atualizando resolução para Câmera {cam_idx} para {settings['width']}x{settings['height']}")
                self.stop_camera_worker(cam_idx)
                self.start_camera_worker(
                    cam_idx,
                    settings['width'],
                    settings['height'],
                    worker.desired_fps # Mantém o FPS anterior para essa câmera
                )


        # Atualiza qual câmera deve ser exibida
        self.camera_exibicao_atual_index = camera_num_to_display_selected_by_user
        print(f"Câmera selecionada para exibição: {self.camera_exibicao_atual_index}")


    def quit_app(self):
        print("Liberando recursos e fechando a aplicação...")
        # Para todas as threads de câmera ativas
        for cam_idx in list(self.camera_workers.keys()): # Itera sobre uma cópia das chaves
            self.stop_camera_worker(cam_idx)
        self.master.destroy()

    def show_error(self, message):
        error_label = tk.Label(self.master, text=message, fg="red", font=("Helvetica", 12))
        error_label.pack(pady=20, padx=20)

if __name__ == "__main__":
    root = tk.Tk()
    app = MainController(root)
    root.mainloop()