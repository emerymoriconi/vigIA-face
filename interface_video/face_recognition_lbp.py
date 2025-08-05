# face_recognition_lbp.py
import cv2

class LBPFaceRecognizer:
   
    def __init__(self, cascade_path='arquivos_algoritmos/lbp/lbpcascade_frontalface.xml'):
        # Carrega o modelo LBP pré-treinado para detecção de faces
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        if self.face_cascade.empty():
            raise IOError(f"Não foi possível carregar o arquivo do classificador LBP: {cascade_path}")

    def process_frame(self, frame):
        """
        Recebe um frame, detecta faces usando LBP e retorna o frame com as anotações.
        """
        # Converte o frame para escala de cinza para melhor desempenho
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # O LBP também usa o detectMultiScale.
        # Os parâmetros podem ser ligeiramente ajustados para otimizar,
        # mas os valores padrão funcionam bem.
        faces = self.face_cascade.detectMultiScale(
            gray_frame, 
            scaleFactor=1.1, 
            minNeighbors=8,  # LBP pode ter um valor de minNeighbors diferente do Haar.
            minSize=(30, 30)
        )

        faces_data = []
        for (x, y, w, h) in faces:
            faces_data.append({"bbox": (x, y, w, h)})
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, "LBP", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return frame, faces_data