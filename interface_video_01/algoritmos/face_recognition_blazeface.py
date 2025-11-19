# face_recognition_blazeface.py
import cv2
import mediapipe as mp

class BlazeFaceDetector:

    def __init__(self):
        # Inicializa a solução de detecção de rostos do MediaPipe.
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            min_detection_confidence=0.5)

    def process_frame(self, frame):
        # A biblioteca MediaPipe espera imagens no formato RGB.
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Processa o frame para detecção.
        results = self.face_detection.process(frame_rgb)

        faces_data = []
        if results.detections:
            for detection in results.detections:
                confidence = detection.score[0]
                bboxC = detection.location_data.relative_bounding_box
                ih, iw, _ = frame.shape

                # Converte as coordenadas normalizadas para pixels.
                x, y, w, h = int(bboxC.xmin * iw), int(bboxC.ymin * ih), int(bboxC.width * iw), int(bboxC.height * ih)
                
                margin = 0.4  # 40%
            
                # Calcular o novo tamanho e posição da caixa
                new_w = int(w * (1 + margin))
                new_h = int(h * (1 + margin))
                new_x = x - int((new_w - w) / 2)
                new_y = y - int((new_h - h) / 2)
                
                # Garantir que a bounding box não saia do frame
                new_x = max(0, new_x)
                new_y = max(0, new_y)
                new_w = min(iw - new_x, new_w)
                new_h = min(ih - new_y, new_h)

                faces_data.append({"bbox": (new_x, new_y, new_w, new_h), "confidence": confidence})

                # Desenhar o novo bounding box com a margem
                cv2.rectangle(frame, (new_x, new_y), (new_x + new_w, new_y + new_h), (255, 0, 255), 2)
                text = f"BlazeFace: {confidence:.2f}"
                cv2.putText(frame, text, (new_x, new_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)

        return frame, faces_data