from picamera2 import Picamera2
import time
import cv2

picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"format": "BGR888", "size": (640, 480)})
picam2.configure(config)

picam2.start()
time.sleep(1)

frame = picam2.capture_array()

# Mostra a imagem com OpenCV
cv2.imshow("Preview", frame)
cv2.waitKey(0)
cv2.destroyAllWindows()
