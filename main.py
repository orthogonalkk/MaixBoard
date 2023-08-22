import os
import time

if __name__ == '__main__':
    time.sleep(5)
    os.chdir('/root/.local/lib/python3.8/site-packages')
    os.system('python demo.py')