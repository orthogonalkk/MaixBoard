import time
import queue

class Event:
    def __init__(self, id = 0, period = 1, interval = 0) -> None:
        self.id = id
        self.period = period # seconds
        self.interval = interval # seconds

    def __str__(self) -> str:
        return '(id: {}, period: {}, interval: {})'.format(self.id, self.period, self.interval)
    
    def __repr__(self) -> str:
        return '(id: {}, period: {}, interval: {})'.format(self.id, self.period, self.interval)


eventQueue = [queue.Queue(maxsize= 8), queue.Queue(maxsize= 8)]

WIFI_NAME = 'Navigation-0001'
WIFI_PASSWORD = '00000000'

global is_connected
global host_ip

def init(): 
    global is_connected, host_ip
    is_connected = False
    host_ip = '192.168.181.43'

def set_ip(ip: str):
    global host_ip
    host_ip = ip

def get_ip():
    global host_ip
    return host_ip

def set_value(value):
    global is_connected
    is_connected = value

def get_value():
    global is_connected
    return is_connected

def wait_for_connected():
    global is_connected
    while not is_connected:
        time.sleep(1)

def wait_for_disconnected():
    global is_connected
    while is_connected:
        time.sleep(1)
