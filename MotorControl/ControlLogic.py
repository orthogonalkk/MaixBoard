from . import GPIOset
from GlobalVar.globalVar import eventQueue, Event
import time
import logging

logging.basicConfig(level=logging.DEBUG)
    

class MotorControl:
    def __init__(self) -> None:
        self.GPIOdict = dict(zip('0123', [GPIOset.Motor0, GPIOset.Motor1,
                                         GPIOset.Motor2, GPIOset.Motor3]))
        GPIOset.Motor0.set_value(0)
        GPIOset.Motor1.set_value(0)
        GPIOset.Motor2.set_value(0)
        GPIOset.Motor3.set_value(0)

    def vibrate_motor(self, instruction):
        if isinstance(instruction, Event):
            self.GPIOdict[str(instruction.id)].set_value(1)
            time.sleep(instruction.period)
            self.GPIOdict[str(instruction.id)].set_value(0)
            time.sleep(instruction.interval)
        else:
            logging.info('unknow instruction: {}, type: {}'.format(instruction, type(instruction)))

def consume_command_routine():
    motor = MotorControl()
    while True:
        while not eventQueue[1].empty(): # deal with the sencond highest priority queue
            while not eventQueue[0].empty(): # deal with the highest priority queue
                try:
                    peek = eventQueue[0].get(timeout= 0.5)
                except Exception as e:
                    logging.info('queue 0 empty!' + str(e))
                logging.info('ultrasonic command: {}'.format(peek))
                motor.vibrate_motor(peek)
            try:
                peek = eventQueue[1].get(timeout= 0.5)
            except Exception as e:
                logging.info('queue 1 empty!' + str(e))
            logging.info('TCP command: {}'.format(peek))
            motor.vibrate_motor(peek)
        time.sleep(1)

