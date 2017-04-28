import subprocess
import time



while(True):
    result = subprocess.run(['sudo', 'iwlist', 'eno1', 'scan'], stdout=subprocess.PIPE)
    if "Android" in result.stdout:
        #THIS means restarting network

    time.sleep(10)
