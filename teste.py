import cv2

cap = cv2.VideoCapture(38)
if not cap.isOpened():
    print("Falha ao abrir câmera USB")
else:
    print("Câmera aberta com sucesso")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow("USB Camera", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
cap.release()
cv2.destroyAllWindows()
