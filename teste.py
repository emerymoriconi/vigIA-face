import cv2
from picamera2 import Picamera2

cascade_path = 'haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(cascade_path)
if face_cascade.empty():
    raise IOError("Não foi possível carregar o Haarcascade.")

picam2 = Picamera2()
config = picam2.create_video_configuration(main={"size": (320, 240), "format": "RGB888"})  # RGB
picam2.configure(config)
print("Configuração da câmera:", config)
print("Propriedades da câmera:", picam2.camera_properties)
picam2.start()

while True:
    frame_rgb = picam2.capture_array("main")
    print("Shape:", frame_rgb.shape)
    print("Dtype:", frame_rgb.dtype)
    print("Primeiros pixels RGB:", frame_rgb[0, 0:5])
    
    frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
    print("Primeiros pixels BGR:", frame_bgr[0, 0:5])

    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    
    for (x, y, w, h) in faces:
        cv2.rectangle(frame_bgr, (x,y), (x+w,y+h), (0,255,0), 2)
    
    cv2.imshow("Face Detection", frame_bgr)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

picam2.stop()
cv2.destroyAllWindows()
