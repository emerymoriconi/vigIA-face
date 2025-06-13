import cv2

class Camera:
   
    def __init__(self, device_index=0):
        
        self.vid = cv2.VideoCapture(device_index, cv2.CAP_DSHOW) 
        if not self.vid.isOpened():
            raise ValueError(f"Não foi possível abrir a câmera no dispositivo {device_index}")

    def set_properties(self, width, height, fps):
       
        self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.vid.set(cv2.CAP_PROP_FPS, fps)
        return self.get_properties()

    def get_properties(self):
        
        width = int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(self.vid.get(cv2.CAP_PROP_FPS))
     
        if fps == 0:
            fps = 30
        return {'width': width, 'height': height, 'fps': fps}

    def get_frame(self):
    
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            if ret:
                return (True, frame)
        return (False, None)

    def release(self):
  
        if self.vid.isOpened():
            self.vid.release()