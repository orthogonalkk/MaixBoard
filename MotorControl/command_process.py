#!/usr/bin/env python
from GlobalVar import globalVar
from .ControlLogic import MotorControl
import socket
import os
import logging
import select

logging.basicConfig(level=logging.DEBUG)

motor = MotorControl()

serverPort = 6666
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.settimeout(5)

server_socket.bind(('', serverPort))
server_socket.listen(1)
logging.info('[**] server is ready!')

def set_network_status(host_ip, status):
    globalVar.set_ip(host_ip[0])
    globalVar.set_value(status)


def TCP_communication():
    try:
        conn, client_address = server_socket.accept()
    except Exception as e:
        logging.info('command_process thread---> TCP error: ' + str(e))
        globalVar.set_value(False)
        os.system('wifi_connect_ap_test' + ' ' + globalVar.WIFI_NAME + ' ' + globalVar.WIFI_PASSWORD)
        return 
    set_network_status(client_address, status= True)
    conn.setblocking(0)
    try:
        while True:
            ready = select.select([conn], [], [], 2)
            raw_data = conn.recv(2048) if ready[0] else None
            if not raw_data:
                break
            motor.begin_event_control(raw_data= raw_data)
        conn.close()
    except Exception as e:
        logging.info('command_process thread---> connnection error: ' + str(e))
        return  

    
    


