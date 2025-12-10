import cv2
from ultralytics import YOLO

class YOLOv8FaceDetector:
    
    def __init__(self, model_path='arquivos_algoritmos/yolo/yolov8n-face.pt'):
        # Carrega o modelo YOLOv8 pré-treinado para detecção de faces
        self.model = YOLO(model_path)
        
        # Confiança mínima para considerar uma detecção válida
        self.confidence_threshold = 0.5 

    def process_frame(self, frame):
        """
        Recebe um frame, detecta faces usando YOLOv8n e retorna o frame com as anotações.
        """
        # Passa o frame pelo modelo para obter as detecções
        results = self.model.predict(
            frame, 
            conf=self.confidence_threshold, 
            verbose=False # Desativa a impressão de logs para o console
        )
        
        faces_data = []
        # Itera sobre os resultados da detecção
        for r in results:
            for box in r.boxes:
                confidence = box.conf[0].item()

                # Pega as coordenadas do bounding box
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                
                # Converte para o formato (x, y, largura, altura)
                x = int(x1)
                y = int(y1)
                w = int(x2 - x1)
                h = int(y2 - y1)

                # Adiciona os dados à lista
                faces_data.append({"bbox": (x, y, w, h), "confidence": confidence})

                # Desenha o retângulo e o texto no frame
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                text = f"YOLOv8: {confidence:.2f}"
                cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        return frame, faces_data