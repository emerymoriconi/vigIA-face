import cv2
from mtcnn.mtcnn import MTCNN

class MTCNNFaceDetector:
    def __init__(self):
        """
        Inicializa o detector MTCNN. O modelo já vem pré-treinado na biblioteca.
        """
        self.detector = MTCNN()

    def process_frame(self, frame):
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # O método detect_faces retorna uma lista de dicionários, onde cada
        # dicionário contém a 'box', a 'confidence' e 'keypoints' de uma face.
        detections = self.detector.detect_faces(rgb_frame)
        
        faces_data = []
        for det in detections:
            # Extrai as coordenadas do bounding box [x, y, largura, altura]
            x, y, w, h = det['box']
            confidence = det['confidence']
            
            # Formata a detecção para a sua estrutura de dados
            faces_data.append({"bbox": (x, y, w, h), "confidence": confidence})
            
            # Desenha o retângulo na imagem original (BGR)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            
            # Adiciona o texto da confiança para referência
            text = f"MTCNN: {confidence:.2f}"
            cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            # (Opcional) Você pode desenhar os pontos de referência do rosto
            keypoints = det['keypoints']
            cv2.circle(frame, keypoints['left_eye'], 2, (0, 155, 255), 2)
            cv2.circle(frame, keypoints['right_eye'], 2, (0, 155, 255), 2)
            cv2.circle(frame, keypoints['nose'], 2, (0, 155, 255), 2)
            cv2.circle(frame, keypoints['mouth_left'], 2, (0, 155, 255), 2)
            cv2.circle(frame, keypoints['mouth_right'], 2, (0, 155, 255), 2)
            
        return frame, faces_data