#!/usr/bin/env python

import time
import subprocess
import sys

subprocess.Popen([sys.executable, 'hiloGPS.py', '--username', 'root'])
subprocess.Popen([sys.executable, 'hiloIMU.py', '--username', 'root'])
time.sleep(10)
subprocess.Popen([sys.executable, 'filtradoGPSIMU.py', '--username', 'root'])
'''
execfile('hiloGPS.py')
execfile('hiloIMU.py')
time.sleep(0.5)
execfile('filtradoGPSIMU.py')
'''
