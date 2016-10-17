#!/usr/bin/env python

import time
import subprocess
import sys

subprocess.Popen([sys.executable, 'hiloGPS.py', '--username', 'root'])
subprocess.Popen([sys.executable, 'hiloIMUpy', '--username', 'root'])
time.sleep(5)
subprocess.Popen([sys.executable, 'filtradoGPSIMU.py', '--username', 'root'])
'''
execfile('hiloGPS.py')
execfile('hiloIMUSinBarometro.py')
time.sleep(0.5)
execfile('filtradoGPSIMU.py')
'''
