import cv2
import logging
import time

logging.basicConfig(level=logging.DEBUG)

class OpenCVCamera():
    def __init__(self, device=0):
        import cv2
        self.cap = cv2.VideoCapture(device)

    def is_opened(self):
        return self.cap.isOpened()
    
    def try_open(self):
        self.cap.open()

    def capture(self):
        _, frame = self.cap.read()
        return frame
    
    def img2bytes(self, img = None, packet_size = 5000):
        if img is None:
            return
        params = [cv2.IMWRITE_JPEG_QUALITY, 80] 
        # img = cv2.resize(img, (320, 240))
        jpg_img = cv2.imencode(".jpg", img, params)[1]
        shape = jpg_img.shape  
        str_shape = ' '.join([str(s) for s in shape]) 
        img_fl = jpg_img.flatten()  # flatten array
        img_bytes = bytes(img_fl)
        byteList = self.subPacket(img_bytes, step= packet_size)
        return str_shape, byteList

    def subPacket(self, obj, step):
        return [obj[i: i+ step] for i in range(0, len(obj), step)]
    
def main():
    camera = OpenCVCamera(device= 2)
    while True:
        try:
            logging.info('[**] start camera thread' + str(camera.cap.isOpened()))
            while camera.cap.isOpened():
                logging.info('get frame')
        except Exception as e:
            logging.info('open camera error!' + str(e))
            camera = OpenCVCamera(device= 2)
            time.sleep(1)

main()