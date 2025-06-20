import cv2

cap = cv2.VideoCapture("/dev/video10")

if not cap.isOpened():
    print("Não foi possível abrir a câmera.")
    exit()

print("Pressione 'q' para sair.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Falha ao capturar frame.")
        break

    cv2.imshow("Câmera - Pressione 'q' para sair", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
