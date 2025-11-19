import tkinter as tk
from gui import GUI
from camera import Camera
from algoritmos.face_recognition_dlibyollo import DLIBYOLLOFaceRecognizer
from performance_monitor import PerformanceMonitor
from config import RESOLUTION_OPTIONS, FPS_OPTIONS
import time
import threading
import cv2
from PIL import Image, ImageTk
from queue import Queue, Empty
import api_client

class CaptureThread(threading.Thread):
    """Thread Producer: Captura frames continuamente"""
    def __init__(self, camera, frame_queue):
        super().__init__(daemon=True)
        self.camera = camera
        self.frame_queue = frame_queue
        self.running = True
        
    def run(self):
        while self.running:
            ret, frame = self.camera.get_frame()
            if ret and frame is not None:
                # Descarta frame antigo se fila cheia (mantém apenas recente)
                if self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()
                    except Empty:
                        pass
                
                try:
                    self.frame_queue.put(frame, block=False)
                except:
                    pass
            time.sleep(0.001)  # 1ms delay mínimo
    
    def stop(self):
        self.running = False

class ProcessingThread(threading.Thread):
    """Thread Consumer: Processa frames da fila"""
    def __init__(self, frame_queue, result_queue, face_recognizer, performance_monitor, processing_mode="local"): # <--- MODIFICADO
        super().__init__(daemon=True)
        self.frame_queue = frame_queue
        self.result_queue = result_queue
        self.face_recognizer = face_recognizer
        self.performance_monitor = performance_monitor
        self.running = True
        
        # Define o modo de processamento com base na seleção da GUI
        self.processing_mode = processing_mode # <--- MODIFICADO
        print(f"ProcessingThread iniciada em modo: {self.processing_mode}")

    def draw_info_card(self, frame, api_response, face_bbox):
        """
        Desenha o card de informações no frame, similar ao da imagem de exemplo.
        """
        frame_h, frame_w, _ = frame.shape
        sidebar_width = 300 # Largura do card
        
        # Evita erro se o frame for menor que o sidebar
        if frame_w < sidebar_width + 20: # Adiciona padding
             # Não desenha o card se o frame for muito pequeno
             return frame 
            
        sidebar_x_start = frame_w - sidebar_width

        # 1. Cria o overlay semi-transparente
        overlay = frame.copy()
        # Cor de fundo escura (B, G, R)
        cv2.rectangle(overlay, (sidebar_x_start, 0), (frame_w, frame_h), (30, 30, 30), -1) 
        alpha = 0.85 # Opacidade
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        
        # Posições e cores
        x_pos = sidebar_x_start + 20 # Padding esquerdo dentro do card
        y_pos = 40
        line_height = 25
        section_break = 35
        
        # Cores (B, G, R)
        COLOR_WHITE = (255, 255, 255)
        COLOR_GREEN = (100, 255, 100)
        COLOR_RED = (100, 100, 255)
        COLOR_BLUE = (255, 200, 100)
        COLOR_GRAY = (180, 180, 180)

        # 2. Pega a BBox do rosto
        x, y, w, h = face_bbox

        # 3. Desenha a Informação
        if api_response and api_response.get('nome_completo'):
            # --- MODO RECONHECIDO ---
            nome = api_response.get('nome_completo', 'N/A').upper()
            fonte = api_response.get('face_source', 'N/A')
            cpf = api_response.get('cpf', 'N/A')
            # O schema da API tem 'nome_mae', mas pode vir nulo
            mae = api_response.get('nome_mae', 'N/A') 
            nasc = api_response.get('data_nascimento', 'N/A')
            idade = str(api_response.get('idade', 'N/A'))

            conf_str = f"{(api_response.get('confiability', 0) * 100):.2f}%"
            eucl_str = f"{api_response.get('euclidian_score', 0):.4f}"
            prob_str = f"{(api_response.get('ia_prob', 0) * 100):.2f}%"

            # Desenha BBox verde no rosto
            cv2.rectangle(frame, (x, y), (x+w, y+h), COLOR_GREEN, 2)
            cv2.putText(frame, nome, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_GREEN, 1, cv2.LINE_AA)


            # --- Escreve no Card ---
            # Nome (tenta quebrar linhas longas)
            max_w = sidebar_width - 40
            words = nome.split()
            lines = []
            current_line = ""
            for word in words:
                (text_w, _), _ = cv2.getTextSize(current_line + word, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                if text_w < max_w:
                    current_line += word + " "
                else:
                    lines.append(current_line)
                    current_line = word + " "
            lines.append(current_line)

            for line in lines:
                cv2.putText(frame, line.strip(), (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_GREEN, 2, cv2.LINE_AA)
                y_pos += line_height

            y_pos += 10 # Espaço extra pós-nome

            # Detalhes
            cv2.putText(frame, f"Fonte: {fonte}", (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_WHITE, 1, cv2.LINE_AA)
            y_pos += line_height
            cv2.putText(frame, f"CPF: {cpf}", (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_WHITE, 1, cv2.LINE_AA)
            y_pos += line_height
            cv2.putText(frame, f"Mae: {mae}", (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_WHITE, 1, cv2.LINE_AA)
            y_pos += line_height
            cv2.putText(frame, f"Nascimento: {nasc}", (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_WHITE, 1, cv2.LINE_AA)
            y_pos += line_height
            cv2.putText(frame, f"Idade: {idade}", (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_WHITE, 1, cv2.LINE_AA)
            y_pos += section_break

            # Linha Separadora
            cv2.line(frame, (x_pos, y_pos), (frame_w - 20, y_pos), COLOR_GRAY, 1)
            y_pos += section_break

            # Scores
            cv2.putText(frame, "Scores de Confianca", (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.55, COLOR_WHITE, 1, cv2.LINE_AA)
            y_pos += line_height + 5

            # Helper para desenhar scores alinhados
            def draw_score(label, value, value_color):
                y = y_pos
                cv2.putText(frame, label, (x_pos, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_GRAY, 1, cv2.LINE_AA)
                (text_w, _), _ = cv2.getTextSize(value, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                cv2.putText(frame, value, (frame_w - text_w - 20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, value_color, 2, cv2.LINE_AA)
                return y + line_height

            y_pos = draw_score("Confiabilidade:", conf_str, COLOR_GREEN)
            y_pos = draw_score("Score Euclidiano:", eucl_str, COLOR_BLUE)
            y_pos = draw_score("Probabilidade IA:", prob_str, COLOR_WHITE)

        else:
            # --- MODO NÃO RECONHECIDO ---
            # Desenha BBox Vermelha
            cv2.rectangle(frame, (x, y), (x+w, y+h), COLOR_RED, 2)

            # --- Escreve no Card ---
            cv2.putText(frame, "NAO RECONHECIDO", (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_RED, 2, cv2.LINE_AA)
            y_pos += section_break
            cv2.putText(frame, "Nenhuma correspondencia", (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_GRAY, 1, cv2.LINE_AA)
            y_pos += line_height
            cv2.putText(frame, "encontrada na API.", (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_GRAY, 1, cv2.LINE_AA)

        return frame

    def run(self):
        while self.running:
            try:
                frame = self.frame_queue.get(timeout=0.5)
                self.performance_monitor.start()
                
                processed_frame = None # Frame que será enviado para a GUI
                faces_data = []      # Dados da detecção
                api_response = None  # Resposta da API
                face_bbox = None     # BBox do rosto principal

                # --- MODO LOCAL (SÓ DETECÇÃO) ---
                if self.processing_mode == "local":
                    processed_frame, faces_data = self.face_recognizer.process_frame(frame.copy())
                
                # --- CENÁRIO 1 (API - BORDA) ---
                elif self.processing_mode == "scenario_1":
                    # 1. Detecção Local
                    # Não desenhamos nada ainda, só pegamos os dados
                    processed_frame_temp, faces_data = self.face_recognizer.process_frame(frame.copy())
                    
                    # O 'processed_frame' base será o frame original
                    processed_frame = frame.copy() 

                    if faces_data:
                        # Pega o primeiro rosto detectado
                        face_info = faces_data[0] 
                        x, y, w, h = face_info['bbox']
                        face_bbox = (x, y, w, h)
                        
                        # Recorta o rosto do frame ORIGINAL (sem anotações)
                        cropped_face = frame[y:y+h, x:x+w]
                        
                        if cropped_face.size > 0:
                            # Codifica o recorte para JPG
                            ret, buffer = cv2.imencode('.jpg', cropped_face)
                            if ret:
                                image_bytes = buffer.tobytes()
                                
                                # 2. Reconhecimento na API
                                api_response = api_client.recognize_cropped_face(image_bytes)
                        
                        # 3. Desenha o Card (função lida com 'None' ou resposta válida)
                        self.draw_info_card(processed_frame, api_response, face_bbox)
                    
                    # Se não houver 'faces_data', 'processed_frame' continua sendo o frame original
                
                # --- CENÁRIO 2 (API - CENTRAL) ---
                elif self.processing_mode == "scenario_2":
                    processed_frame = frame.copy() 

                    # 1. Codifica o FRAME INTEIRO (com compressão)
                    ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    if ret:
                        image_bytes = buffer.tobytes()

                        # 2. Chama a nova função do api_client
                        api_response = api_client.recognize_full_frame(image_bytes)

                        # 3. Processa a resposta da API (que agora inclui a 'bbox')
                        if api_response and api_response.get('nome_completo') and api_response.get('bbox'):
                            bbox_raw = api_response.get('bbox')

                            # Converte a bbox [x1, y1, x2, y2] para (x, y, w, h)
                            x = int(bbox_raw[0])
                            y = int(bbox_raw[1])
                            w = int(bbox_raw[2] - x)
                            h = int(bbox_raw[3] - y)
                            face_bbox = (x, y, w, h)

                            # 4. Desenha o card de informações no frame
                            self.draw_info_card(processed_frame, api_response, face_bbox)

                self.performance_monitor.stop_and_record()
                
                # --- Envio para GUI ---
                if processed_frame is None:
                    processed_frame = frame # Garante que a GUI sempre receba um frame
                    
                if self.result_queue.full():
                    try: self.result_queue.get_nowait()
                    except Empty: pass
                
                try:
                    self.result_queue.put(processed_frame, block=False)
                except:
                    pass
                    
            except Empty:
                continue
            except Exception as e:
                print(f"Erro no processamento: {e}")
    
    def stop(self):
        self.running = False
        
class CameraFeedController:
    def __init__(self, master, camera_info, resolution_settings, desired_fps, face_recognizer_instance, processing_mode): # <--- MODIFICADO
        """
        Args:
            camera_info: Dict com {index, name, type, use_opencv}
            processing_mode: String ('local', 'scenario_1', etc.)
        """
        self.master = master
        self.camera_info = camera_info
        self.camera_index = camera_info['index']
        
        self.master.title(f"[{camera_info['type']}] {camera_info['name']}")

        self.desired_fps = desired_fps
        self.running = True
        self.performance_monitor = PerformanceMonitor()

        try:
            # Inicializa câmera
            self.camera = Camera(
                camera_index=self.camera_index,
                use_opencv=camera_info['use_opencv']
            )
            
            actual_camera_props = self.camera.set_properties(
                width=resolution_settings['width'],
                height=resolution_settings['height'],
            )

            # Cria filas (pequenas para baixa latência)
            self.frame_queue = Queue(maxsize=2)    # Buffer de captura
            self.result_queue = Queue(maxsize=1)   # Buffer de resultado
            
            # Inicia threads Producer-Consumer
            self.capture_thread = CaptureThread(self.camera, self.frame_queue)
            self.processing_thread = ProcessingThread(
                self.frame_queue, 
                self.result_queue, 
                face_recognizer_instance,
                self.performance_monitor,
                processing_mode # <--- PASSANDO O MODO PARA A THREAD
            )
            
            self.capture_thread.start()
            self.processing_thread.start()
            
            self.video_gui = VideoFeedGUI(master)
            self.master.protocol("WM_DELETE_WINDOW", self.quit_app)

            print(f"Câmera {self.camera_index} iniciada: {actual_camera_props}")

            # Loop de exibição (busca resultados processados)
            self.delay = 15  # ~60 FPS de atualização da GUI
            self.update_display()

        except Exception as e:
            self.show_error(str(e))

    def update_display(self):
        """Loop de exibição: busca frames processados e exibe"""
        if not self.running:
            return
        
        # Tenta pegar frame processado
        try:
            processed_frame = self.result_queue.get_nowait()
            self.video_gui.update_video_frame(processed_frame)
        except Empty:
            pass  # Nenhum frame novo, ok
        
        self.master.after(self.delay, self.update_display)

    def quit_app(self):
        print(f"Liberando câmera {self.camera_index}...")
        self.running = False
        
        # Para threads
        self.capture_thread.stop()
        self.processing_thread.stop()
        
        # Aguarda finalização
        self.capture_thread.join(timeout=2)
        self.processing_thread.join(timeout=2)
        
        self.print_and_save_summary()
        self.camera.release()
        self.master.destroy()
        
    def print_and_save_summary(self):
        summary = self.performance_monitor.get_summary()
        if summary:
            print("\n" + "="*40)
            print(f"  Câmera {self.camera_index} - DESEMPENHO")
            print("="*40)
            print(f"Frames processados: {summary['total_frames']}")
            print(f"Tempo Médio: {summary['avg_processing_time_ms']:.2f} ms")
            print(f"CPU Média: {summary['avg_cpu_percent']:.2f} %")
            print("="*40 + "\n")

            settings = self.get_current_settings()
            self.performance_monitor.save_to_file(
                "DLIBYOLLOFaceRecognizer", 
                settings
            )

    def get_current_settings(self):
        return {
            "width": self.camera.get_properties()['width'],
            "height": self.camera.get_properties()['height'],
            "desired_fps": self.desired_fps
        }

    def show_error(self, message):
        error_label = tk.Label(self.master, text=message, fg="red", font=("Helvetica", 12))
        error_label.pack(pady=20, padx=20)


class VideoFeedGUI:
    def __init__(self, master):
        self.master = master
        self.canvas = tk.Canvas(master, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.photo = None

    def update_video_frame(self, frame):
        h, w, _ = frame.shape
        self.canvas.config(width=w, height=h)
        
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img)
        self.photo = ImageTk.PhotoImage(image=img_pil)
        
        self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Controle Central de Câmeras")

        # Detecta câmeras
        self.available_cameras = Camera.detect_available_cameras()
        
        self.gui = GUI(
            root, 
            available_cameras=self.available_cameras,
            title="Controle Central de Câmeras"
        )
        self.gui.set_callbacks(self.apply_settings, self.quit_app)

        self.camera_controllers = []
        self.launch_threads = []
        
        # Recognizer por câmera (evita concorrência)
        self.face_recognizers = {}

    def _launch_single_camera_controller(self, camera_info, resolution_settings, desired_fps, processing_mode): # <--- MODIFICADO
        """Lança controlador em nova janela"""
        cam_idx = camera_info['index']
        
        # Cria recognizer para esta câmera
        self.face_recognizers[cam_idx] = DLIBYOLLOFaceRecognizer()
        
        top_level = tk.Toplevel(self.root)
        controller = CameraFeedController(
            top_level, 
            camera_info, 
            resolution_settings, 
            desired_fps, 
            self.face_recognizers[cam_idx],
            processing_mode # <--- PASSANDO O MODO
        )
        self.camera_controllers.append(controller)

    def apply_settings(self):
        settings = self.gui.get_settings()
        if not settings:
            print("Configurações inválidas")
            return

        self._shutdown_all_cameras()

        resolution_settings = {
            'width': settings['width'], 
            'height': settings['height']
        }
        desired_fps = settings['desired_fps']
        processing_mode = settings['processing_mode'] # <--- PEGANDO O MODO DA GUI

        if settings['mode'] == "Câmera Única":
            if settings['camera_info']:
                thread = threading.Thread(
                    target=self._launch_single_camera_controller,
                    args=(settings['camera_info'], resolution_settings, desired_fps, processing_mode) # <--- PASSANDO O MODO
                )
                self.launch_threads.append(thread)
                thread.start()
                
        elif settings['mode'] == "Múltiplas Câmeras":
            if desired_fps > 15:
                print("FPS reduzido para 15 (múltiplas câmeras)")
                desired_fps = 15
            
            for camera_info in self.available_cameras:
                thread = threading.Thread(
                    target=self._launch_single_camera_controller,
                    args=(camera_info, resolution_settings, desired_fps, processing_mode) # <--- PASSANDO O MODO
                )
                self.launch_threads.append(thread)
                thread.start()
                time.sleep(0.5)

        print(f"Modo '{settings['mode']}' e Modo Proc. '{processing_mode}' aplicado")

    def _shutdown_all_cameras(self):
        for controller in self.camera_controllers:
            if controller.running:
                controller.quit_app()

        self.camera_controllers = []
        self.launch_threads = []
        self.face_recognizers = {}
        time.sleep(1)

    def quit_app(self):
        print("Fechando aplicação...")
        self._shutdown_all_cameras()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()

