# face_recognition_ssd.py
import cv2
import numpy as np

class SSDFaceDetector:
   
    def __init__(self, prototxt_path='arquivos_algoritmos/ssd/deploy.prototxt', model_path='arquivos_algoritmos/ssd/res10_300x300_ssd_iter_140000_fp16.caffemodel'):
        # Carrega a rede neural SSD pré-treinada para detecção de faces
        self.net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
        
        # O SSD foi treinado com imagens de 300x300 pixels
        self.input_size = (300, 300)
        
        # Confiança mínima para considerar uma detecção válida
        self.confidence_threshold = 0.5 

    def process_frame(self, frame):
        """
        Recebe um frame, detecta faces usando SSD e retorna o frame com as anotações.
        """
        (h, w) = frame.shape[:2]
        
        # Prepara o frame para o modelo SSD (cria um "blob")
        # O blob é uma representação da imagem que pode ser passada para a rede
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, self.input_size), 1.0, 
                                     self.input_size, (104.0, 177.0, 123.0))

        # Passa o blob pela rede para obter as detecções
        self.net.setInput(blob)
        detections = self.net.forward()

        faces_data = []
        # Itera sobre as detecções
        for i in range(0, detections.shape[2]):
            confidence = detections[0, 0, i, 2]

            # Filtra detecções fracas pela confiança
            if confidence > self.confidence_threshold:
                # Pega as coordenadas do bounding box e as escala para o tamanho original do frame
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")

                # Adiciona os dados à lista
                faces_data.append({"bbox": (startX, startY, endX - startX, endY - startY), 
                                   "confidence": confidence})

                # Desenha o retângulo e o texto no frame
                cv2.rectangle(frame, (startX, startY), (endX, endY), (255, 255, 0), 2)
                text = f"SSD: {confidence:.2f}"
                cv2.putText(frame, text, (startX, startY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
        
        return frame, faces_data