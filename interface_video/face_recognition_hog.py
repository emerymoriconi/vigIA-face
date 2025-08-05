import cv2
import dlib 

class HOGFaceRecognizer:
   
    def __init__(self):
        # O dlib já vem com um detector de faces frontais pré-treinado.
        # Não é necessário um arquivo .xml como no Haar Cascades.
        self.detector = dlib.get_frontal_face_detector()

    def process_frame(self, frame):
        # Converte para escala de cinza
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # O detector do dlib retorna uma lista de retângulos (faces)
        # O '1' no parâmetro 'upsample_num_times' instrui o detector a
        # fazer um upsampling da imagem 1 vez, o que ajuda a encontrar
        # faces menores, mas consome mais CPU. Para um teste de desempenho,
        # você pode começar com 0.
        faces = self.detector(gray_frame, 0)

        faces_data = []
        for face_rect in faces:
            # O dlib retorna um objeto 'dlib.rectangle'.
            # Precisamos extrair as coordenadas (x, y, largura, altura).
            x1, y1 = face_rect.left(), face_rect.top()
            x2, y2 = face_rect.right(), face_rect.bottom()
            width, height = x2 - x1, y2 - y1
            
            # Adiciona os dados à lista de retorno
            faces_data.append({"bbox": (x1, y1, width, height)})

            # Desenha o bounding box no frame original
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            
            # Adiciona o texto do algoritmo para identificação visual
            cv2.putText(frame, "HOG", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        return frame, faces_data