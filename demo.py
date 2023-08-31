from CameralControl.camera_process import camera_thread_routine
from TCPControl.command_process import TCP_communication
from BroadcastControl.broadcast_process import broadcast_thread_routine
from MotorControl.ControlLogic import consume_command_routine
from Ultrasonic.Ultrasonic import ultrasonic_routine
import GlobalVar.globalVar as globalVar
from threading import Thread
import time
import os

globalVar.init()

if __name__ == '__main__':
    os.system('echo "usb_host" > /sys/devices/platform/soc/usbc0/otg_role')
    os.system('wifi_connect_ap_test' + ' ' + globalVar.WIFI_NAME + ' ' + globalVar.WIFI_PASSWORD)
    time.sleep(2)
    Thread(target= ultrasonic_routine).start()
    Thread(target= consume_command_routine).start()
    Thread(target= broadcast_thread_routine).start()
    Thread(target= camera_thread_routine).start()
    while True:
        try:
            TCP_communication()
        except Exception as e:
            print('main thread error ' + str(e))
            print('network disconnected !!!')
            globalVar.set_value(False)
            os.system('wifi_connect_ap_test' + ' ' + globalVar.WIFI_NAME + ' ' + globalVar.WIFI_PASSWORD)