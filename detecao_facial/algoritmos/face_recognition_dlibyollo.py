import cv2
import dlib
from ultralytics import YOLO
import numpy as np

class DLIBYOLLOFaceRecognizer:
   
    def __init__(self):
        """
        Inicializa o pipeline hierárquico com identificação por landmarks.
        - Estágio 1: Detector de faces HOG do Dlib (para localização inicial).
        - Estágio 2: Preditor de landmarks Dlib (para criar uma ROI precisa).
        - Estágio 3: Detector de faces YOLOv8 (para detecção final na ROI).
        """
      
        self.dlib_detector = dlib.get_frontal_face_detector()

        
        predictor_path = "arquivos_algoritmos/dlibyollo/shape_predictor_68_face_landmarks.dat"
        self.shape_predictor = dlib.shape_predictor(predictor_path)

       
        model_path = 'arquivos_algoritmos/yolo/yolov8n-face.pt'
        self.yolo_model = YOLO(model_path)
        self.confidence_threshold = 0.5

    def process_frame(self, frame):
        """
        Processa um frame: Dlib HOG -> Dlib Landmarks para ROI -> Expansão -> YOLOv8.
        """
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_h, frame_w = frame.shape[:2]
        
        # --- ESTÁGIO 1: Detecção Rápida com Dlib (Localização Inicial) ---
        initial_hog_rects = self.dlib_detector(gray_frame, 0)

        final_faces_data = []
        for hog_rect in initial_hog_rects:
            
            # --- ESTÁGIO 2: Identificação com Pontos e Criação da ROI Precisa ---
            landmarks = self.shape_predictor(gray_frame, hog_rect)
            
            # Converte os landmarks para um array NumPy e desenha na tela.
            landmark_points = np.array([[p.x, p.y] for p in landmarks.parts()])
            for x, y in landmark_points:
                cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)

            # Cria uma Box precisa a partir dos pontos extremos dos landmarks.
            x1_lm, y1_lm = landmark_points.min(axis=0)
            x2_lm, y2_lm = landmark_points.max(axis=0)

            # --- Expansão da ROI baseada nos Landmarks ---
            # Expande a ROI para garantir que a testa e o queixo sejam incluídos.
            padding_w = (x2_lm - x1_lm) * 0.50  # Expande 50% da largura
            padding_h = (y2_lm - y1_lm) * 0.50  # Expande 50% da altura (mais para testa/queixo)

            x1 = int(max(0, x1_lm - padding_w))
            y1 = int(max(0, y1_lm - padding_h))
            x2 = int(min(frame_w, x2_lm + padding_w))
            y2 = int(min(frame_h, y2_lm + padding_w)) # Usa padding da largura para as laterais
            
            # Recorta a ROI aprimorada e expandida do frame original.
            face_roi_img = frame[y1:y2, x1:x2]

            if face_roi_img.shape[0] == 0 or face_roi_img.shape[1] == 0:
                continue

            # --- ESTÁGIO 3: Detecção com YOLOv8 na ROI  ---
            results = self.yolo_model.predict(
                face_roi_img, 
                conf=self.confidence_threshold, 
                verbose=False
            )
            
            yolo_found_face = False
            if results and len(results[0].boxes) > 0:
                yolo_found_face = True
                box = results[0].boxes[0]
                confidence = box.conf[0].item()

                local_x1, local_y1, local_x2, local_y2 = box.xyxy[0].tolist()
                
                # Mapeia as coordenadas daBBox do YOLO de volta para o frame global.
                global_x1 = int(x1 + local_x1)
                global_y1 = int(y1 + local_y1)
                global_x2 = int(x1 + local_x2)
                global_y2 = int(y1 + local_y2)
                
                bbox = (global_x1, global_y1, global_x2 - global_x1, global_y2 - global_y1)

                # Desenha o retângulo final e preciso do YOLO (em azul).
                cv2.rectangle(frame, (global_x1, global_y1), (global_x2, global_y2), (255, 0, 0), 2)
                text = f"YOLO: {confidence:.2f}"
                cv2.putText(frame, text, (global_x1, global_y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

            # Se o YOLO não confirmar a face, podemos opcionalmente pular ou usar a bbox dos landmarks.
            # Aqui, só adicionaremos os dados se o YOLO confirmar a face.
            if yolo_found_face:
                final_faces_data.append({
                    "bbox": bbox, 
                    "confidence": confidence,
                    "landmarks": landmark_points.tolist()
                })
        
        return frame, final_faces_data