#!/usr/bin/env python

class User(object):
    def __init__(self, name, username):
        self.name = name
        self.username = username

import sys
import serial

def init():
    ser = serial.Serial()
    ser.baudrate = 4800
    ser.port = '/dev/ttyUSB0'

    #ser.open()

    #if not ser.isOpen():
    #print("Unable to open serial port!")
    #raise SystemExit

    fo = open("datos.txt", "r+")
    line = fo.readline()
    guardar = open("/media/kevin/guardar.txt", "w")
    while line != "":
        guardar.write(line)
        if (line.startswith('$GPGGA')):
            print("$GPGGA")
            GGA = line.split(',')
            print(GGA[1])
            print(GGA[2] + " " + GGA[3])
            print(GGA[4] + " "+ GGA[5])
            print(GGA[7])
            print(GGA[8])
            print(GGA[9])
            isChanged = True
        if (line.startswith('$GPRMC')):
            print("$GPRMC")
            RMC = line.split(',')
            print(RMC[1])
            print(RMC[2])
            _knots = RMC[7]
            print(RMC[8])
            print(RMC[9])
        line = fo.readline()
        #if isChanged:
        #r = requests.post(self.restDbUrl+'/post/GPS', data=json.dumps(self.GPS), headers={'Content-Type': 'application/json'})
        #if r.status_code != 200:
        #self._writeErr(r.text)
    fo.close()


try:
    init()
except KeyboardInterrupt:
    print "Done."
