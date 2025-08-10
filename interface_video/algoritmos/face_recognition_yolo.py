# face_recognition_yolo.py
import cv2
import numpy as np

class YOLOFaceDetector:

    def __init__(self, config_path='arquivos_algoritmos/yolo/yolov3-tiny.cfg', weights_path='arquivos_algoritmos/yolo/yolov3-tiny.weights', names_path='arquivos_algoritmos/yolo/coco.names'):
        # Carrega o modelo YOLO do Darknet
        self.net = cv2.dnn.readNet(weights_path, config_path)
        
        # Carrega os nomes das classes
        with open(names_path, 'r') as f:
            self.classes = [line.strip() for line in f.readlines()]
            
        # O ID da classe "pessoa" (person) é 0 na lista COCO
        self.person_class_id = self.classes.index("person") if "person" in self.classes else -1

    def process_frame(self, frame):
        """
        Recebe um frame, detecta faces (na verdade, pessoas) usando YOLOv3-tiny e
        retorna o frame com as anotações.
        """
        if self.person_class_id == -1:
            print("Classe 'person' não encontrada no arquivo coco.names.")
            return frame, []

        (h, w) = frame.shape[:2]
        
        # Prepara o frame para o modelo YOLO
        # O YOLOv3-tiny foi treinado com imagens de 416x416
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416), swapRB=True, crop=False)
        self.net.setInput(blob)
        
        # Nomes das camadas de saída para o modelo YOLOv3
        layer_names = self.net.getLayerNames()
        output_layers_indices = self.net.getUnconnectedOutLayers()
        output_layers = [layer_names[i - 1] for i in output_layers_indices]
        
        # Passa o blob pela rede
        outputs = self.net.forward(output_layers)

        boxes = []
        confidences = []
        class_ids = []

        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                # Considera apenas detecções da classe "person" com confiança acima de 0.5
                if class_id == self.person_class_id and confidence > 0.5:
                    box = detection[0:4] * np.array([w, h, w, h])
                    (center_x, center_y, width, height) = box.astype("int")
                    x = int(center_x - (width / 2))
                    y = int(center_y - (height / 2))
                    
                    boxes.append([x, y, int(width), int(height)])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)
        
        # Aplica a Supressão Não Máxima para remover bounding boxes sobrepostas
        indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
        
        faces_data = []
        if len(indices) > 0:
            for i in indices.flatten():
                (x, y, w, h) = boxes[i]
                confidence = confidences[i]
                
                faces_data.append({"bbox": (x, y, w, h), "confidence": confidence})

                # Desenha o retângulo e a confiança
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
                text = f"YOLO: {confidence:.2f}"
                cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                
        return frame, faces_data