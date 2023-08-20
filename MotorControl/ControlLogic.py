from . import GPIOset
from . import V831Message_pb2 as pb
import time
import queue

import logging

logging.basicConfig(level=logging.DEBUG)

class Event:
    def __init__(self, id = 0, period = 1, interval = 0) -> None:
        self.id = id
        self.period = period # seconds
        self.interval = interval # seconds

    def __str__(self) -> str:
        return '(id: {}, period: {}, interval: {})'.format(self.id, self.period, self.interval)
    
    def __repr__(self) -> str:
        return '(id: {}, period: {}, interval: {})'.format(self.id, self.period, self.interval)


class MotorControl:
    def __init__(self) -> None:
        self.GPIOdict = dict(zip('0123', [GPIOset.Motor0, GPIOset.Motor1, GPIOset.Motor2, GPIOset.Motor3]))
        GPIOset.Motor0.set_value(0)
        GPIOset.Motor1.set_value(0)
        GPIOset.Motor2.set_value(0)
        GPIOset.Motor3.set_value(0)
    
    def extract_message(self, raw_data = None):
        if raw_data is None:
            logging.info('got illegal message!')
            return
        msg = pb.V831Message()
        msg.ParseFromString(raw_data)
        if not msg.HasField('content'):
            logging.info("Unexpected missing field (content), skip.")
        msg_name = msg.WhichOneof("content")
        if msg_name == 'heart_beat':
            return
        data = msg.__getattribute__(msg_name)
        eventQueue = queue.Queue(maxsize= 8)
        for event in data.events:
            eventQueue.put( Event(event.motor_id, event.period, event.interval))
        return eventQueue, data.periodic, data.repeated_times

    def vibrate_motor(self, instruction):
        if isinstance(instruction, Event):
            self.GPIOdict[str(instruction.id)].set_value(1)
            time.sleep(instruction.period)
            self.GPIOdict[str(instruction.id)].set_value(0)
            time.sleep(instruction.interval)
        else:
            logging.info('unknow instruction: {}, type: {}'.format(instruction, type(instruction)))
    
    def begin_event_control(self, raw_data = None, count = 0):
        try:
            if self.extract_message(raw_data) is None:
                return
            eventQueue, periodic, repeat_times = self.extract_message(raw_data)
            if not periodic:
                while not eventQueue.empty():
                    self.vibrate_motor(eventQueue.get())
            else:
                while repeat_times > 0:
                    peek = eventQueue.get()
                    eventQueue.put(peek)
                    self.vibrate_motor(peek) 
                    repeat_times -= 1
            logging.info(f'Your {count}th command has been processed')
        except Exception as e:
            logging.info('illigal event----',e)
            return