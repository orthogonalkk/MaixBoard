import socket
import time
from GlobalVar import globalVar

UDP_PORT = 11451
globalVar.init()

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


def broadcast_thread_routine():
    while True:
        while not globalVar.is_connected:
            broadcast_identity()
            time.sleep(1)
        globalVar.wait_for_disconnected()
