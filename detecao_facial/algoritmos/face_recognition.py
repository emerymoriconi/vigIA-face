import cv2

class ViolaFaceRecognizer:
   
    def __init__(self, cascade_path='arquivos_algoritmos/viola-jones/haarcascade_frontalface_default.xml'):
        # Carrega o modelo pré-treinado para detecção de faces frontais
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        if self.face_cascade.empty():
            raise IOError(f"Não foi possível carregar o arquivo do classificador Haar: {cascade_path}")

    def process_frame(self, frame):

        #Recebe um frame, detecta faces e retorna o frame com as anotações  e os dados das faces encontradas.
        # Converte o frame para escala de cinza para melhor desempenho na detecção
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detecta faces no frame
        # scaleFactor: Reduz o tamanho da imagem em 1.3x a cada passo
        # minNeighbors: Quantos "vizinhos" cada retângulo candidato deve ter para ser retido
        # minSize: Tamanho mínimo do objeto a ser detectado
        faces = self.face_cascade.detectMultiScale(gray_frame, scaleFactor=1.3, minNeighbors=5, minSize=(30, 30))

        # Desenha as bounding boxes e os dados no frame original
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            face_data_text = f"Pos:({x},{y}) Dim:({w}x{h})"
            cv2.putText(frame, face_data_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
        return frame, faces