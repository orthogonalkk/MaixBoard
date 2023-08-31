import serial

try:
    print('aaaaa')
    ser = serial.Serial('/dev/ttyS1', 9600, timeout= 0.5)
    print('ddddd')
    print('open serial...')
    while True:
        data = ser.read(4)
        print('data = {}'.format(str(data)))
        for i in data:
            print(i)
except Exception as e:
    print('serial error: ' + str(e))