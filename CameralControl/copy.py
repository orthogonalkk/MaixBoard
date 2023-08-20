import time
import socket
import asyncio
from abc import ABC, abstractmethod
import cv2

from maix import mjpg, utils

UDP_PORT = 11451
MJPG_PORT = 18811


class MyCamera(ABC):
    @abstractmethod
    def capture(self):
        pass


class MaixCamera(MyCamera):
    def capture(self):
        from maix import camera

        return camera.capture()


class OpenCVCamera(MyCamera):
    def __init__(self, device=0):
        import cv2

        self.cap = cv2.VideoCapture(device)

    def capture(self):
        _, frame = self.cap.read()
        return frame
    
    def img2bytes(self, img = None, packet_size = 5000):
        if img is None:
            return
        params = [cv2.IMWRITE_JPEG_QUALITY, 100] 
        img = cv2.resize(img, (320, 240))
        jpg_img = cv2.imencode(".jpg", img, params)[1]
        shape = jpg_img.shape  
        str_shape = ' '.join([str(s) for s in shape]) 
        img_fl = jpg_img.flatten()  # flatten array
        img_bytes = bytes(img_fl)
        byteList = self.subPacket(img_bytes, step= packet_size)
        return str_shape, byteList

    def subPacket(self, obj, step):
        return [obj[i: i+ step] for i in range(0, len(obj), step)]


# Camera = OpenCVCamera(device= 2)


def get_host_ip():
    so = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    so.connect(("10.255.255.255", 1))
    return str(so.getsockname()[0])


def make_broadcast_ip(ip):
    ip = ip.split(".")
    ip[-1] = "255"
    return ".".join(ip)


def make_identity():
    return b"V831"


def broadcast_identity():
    ip = make_broadcast_ip(get_host_ip())
    address = (ip, UDP_PORT)
    so = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    so.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    so.sendto(make_identity(), address)
    so.close()

def set_socket():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    server_port = 38892
    hostname = '192.168.181.255'
    addr = (hostname, server_port)
    return client_socket, addr

async def run_jpeg_client():
    ip = get_host_ip()
    camera = OpenCVCamera(device= 2)
    client_socket, address = set_socket()
    while True:
        try:
            _, byteList = camera.img2bytes(camera.capture())
            # client_socket.sendto(str_shape.encode('utf-8'), address)
            for by in byteList:
                client_socket.sendto(by, address)
            client_socket.sendto(b'end', address)
            print('send an image!')
        except Exception as e:
            print(e)
        await asyncio.sleep(0)
    
    # ip = get_host_ip()
    # camera = MaixCamera(device= 2)
    # queue = mjpg.Queue(maxsize=1)
    # mjpg.MjpgServerThread(ip, MJPG_PORT, mjpg.BytesImageHandlerFactory(q=queue)).start()
    # camera = Camera()
    # while True:
    #     img = camera.capture()
    #     jpg = utils.rgb2jpg(img.convert("RGB").tobytes(), img.width, img.height)
    #     queue.put(mjpg.BytesImage(jpg))
    #     await asyncio.sleep(0)


async def run_broadcast():
    while True:
        broadcast_identity()
        await asyncio.sleep(1)


def main():
    # 如果尚未连接网络，则该函数直接失败，致使系统软重启。
    get_host_ip()
    # 已连接网络，创建协程调度器。
    loop = asyncio.get_event_loop()
    tasks = [
        run_jpeg_client(),
        run_broadcast(),
    ]
    loop.run_until_complete(asyncio.wait(tasks))


def embedded_real_main():
    while True:
        try:
            print('[**] start camera thread')
            main()
        except Exception as e:
            print(e)
            print("Exception occurred in camera process, try soft reset...")
            time.sleep(1)
        print("Soft reset applied, rerun main()")


# if __name__ == "__main__":
#     embedded_real_main()
