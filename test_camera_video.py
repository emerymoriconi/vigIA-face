from picamera2 import Picamera2
import cv2
import time

# Inicializa a câmera
picam2 = Picamera2()

# Cria a configuração de pré-visualização
config = picam2.create_preview_configuration(main={"format": "BGR888", "size": (640, 480)})
picam2.configure(config)

# Inicia a câmera
picam2.start()
time.sleep(1)  # Espera um pouco para garantir que a câmera está pronta

# Loop de captura ao vivo
while True:
    frame = picam2.capture_array()
    cv2.imshow("Camera - Pressione 'q' para sair", frame)

    # Sai se a tecla 'q' for pressionada
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Libera os recursos
cv2.destroyAllWindows()
picam2.stop()
