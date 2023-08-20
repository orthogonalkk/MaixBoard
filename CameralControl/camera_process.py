import time
import socket
import cv2
from GlobalVar import globalVar
import logging

logging.basicConfig(level=logging.DEBUG)

UDP_PORT = 38892

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
        params = [cv2.IMWRITE_JPEG_QUALITY, 100] 
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

def set_udp_socket():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    hostname = globalVar.get_ip()
    addr = (hostname, UDP_PORT)
    return client_socket, addr

def send_jpeg_img(client_socket, address: tuple, camera : OpenCVCamera):
    _, byteList = camera.img2bytes(camera.capture())
    if byteList is None:
        return 
    for by in byteList:
        client_socket.sendto(by, address)  
    client_socket.sendto(b'end', address)
    logging.info('send an image!')

def camera_thread_routine():
    while True:
        globalVar.wait_for_connected()
        time.sleep(1)
        client_socket, address = set_udp_socket()
        while globalVar.get_value():
            try:
                camera = OpenCVCamera(device= 2)
                logging.info('[**] start camera thread')
                while camera.cap.isOpened():
                    send_jpeg_img(client_socket= client_socket, address= address, camera= camera)
            except Exception as e:
                logging.info('open camera error!')
                camera = OpenCVCamera(device= 2)
                time.sleep(1)