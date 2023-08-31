import serial
from GlobalVar.globalVar import eventQueue, Event
import logging

logging.basicConfig(level=logging.DEBUG)

UP =1
LEFT = 0
RIGHT = 2
DOWN =3
threshold = 1.5
countinuous_num = 2
Devices = ['/dev/ttyS1']
baudrate = 9600

def send_command(direction = DOWN, period =0.3, interval = 0):
    eventQueue[0].put_nowait(Event(id = direction, period= period, interval= interval))

def init_serial():
    ser = serial.Serial(Devices[0], baudrate= baudrate, timeout= 0.5)
    return [ser]

def get_distance(ultrasonic : serial) -> float: 
    data = ultrasonic.read(4)
    return round((data[1]*256 + data[2])/1000, 3)

def ultrasonic_routine():
    while True:
        distance1 = []
        try:
            ultrasonics = init_serial()
            while True:
                try:
                    if len(distance1) > countinuous_num:
                        distance1 = distance1[-countinuous_num :]
                        logging.info('distance: ' + str(distance1))
                    if len(distance1) == countinuous_num and all(i < threshold for i in distance1):
                        send_command()
                    d = get_distance(ultrasonics[0])
                    distance1.append(d) if (d > 0.27 and d < 4.6) else None
                except Exception as e:
                    logging.info('serial read error -> ' + str(e))
                    ultrasonics = init_serial()
        except Exception as e:
            logging.info('serial error ->' + str(e))




