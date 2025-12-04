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
    def __init__(self, frame_queue, result_queue, face_recognizer, performance_monitor):
        super().__init__(daemon=True)
        self.frame_queue = frame_queue
        self.result_queue = result_queue
        self.face_recognizer = face_recognizer
        self.performance_monitor = performance_monitor
        self.running = True
        
    def run(self):
        while self.running:
            try:
                # Pega frame da fila (timeout 0.5s)
                frame = self.frame_queue.get(timeout=0.5)
                
                # Processa
                self.performance_monitor.start()
                processed_frame, faces_data = self.face_recognizer.process_frame(frame)
                self.performance_monitor.stop_and_record()
                
                # Coloca resultado (descarta antigo se cheio)
                if self.result_queue.full():
                    try:
                        self.result_queue.get_nowait()
                    except Empty:
                        pass
                
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
    def __init__(self, master, camera_info, resolution_settings, desired_fps, face_recognizer_instance):
        """
        Args:
            camera_info: Dict com {index, name, type, use_opencv}
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
                self.performance_monitor
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

    def _launch_single_camera_controller(self, camera_info, resolution_settings, desired_fps):
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
            self.face_recognizers[cam_idx]
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

        if settings['mode'] == "Câmera Única":
            if settings['camera_info']:
                thread = threading.Thread(
                    target=self._launch_single_camera_controller,
                    args=(settings['camera_info'], resolution_settings, desired_fps)
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
                    args=(camera_info, resolution_settings, desired_fps)
                )
                self.launch_threads.append(thread)
                thread.start()
                time.sleep(0.5)

        print(f"Modo '{settings['mode']}' aplicado")

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