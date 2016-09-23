#!/usr/bin/env python

import serial
import math
import atexit
import redis
import json

def toDoubleLatLong(latlon, side):
    val = None
    try:
        tmp = float(latlon)
        tmp /= 100
        val = math.floor(tmp)
        tmp = (tmp - val) * 100
        val += tmp/60
        tmp -= math.floor(tmp)
        tmp *= 60
        if ((side.upper() == "S") or (side.upper()=="W")):
            val *= -1
    except ValueError:
        print("Can't calculate from {0} side {1}".format(latlon, side))
        val = None
    return val

ser = serial.Serial()
ser.baudrate = 9600
ser.port = '/dev/ttyACM0'
almacenamientoRedis = redis.StrictRedis(host='localhost', port=6379, db=0)

def toFloat(self, value):
    val = None
    if self._isNoneOrEmptry(value):
        return None
    try:
        val = float(value)
    except ValueError:
        self._writeErr("Can't convert to float: {0}".format(value))
        val = None
    return val

def finalizar():
    print("FIN")

atexit.register(finalizar)

ser.open()

if not ser.isOpen():
    print("Unable to open serial port!")
    raise SystemExit

#Pone el GPS a la frecuencia de 2hz
ser.write("\xB5\x62\x06\x08\x06\x00\xF4\x01\x01\x00\x01\x00\x0B\x77")
ser.readline()
fichero = open("/media/card/gpsPrueba.txt", "wb")
primera = True
global fichero
while True:
    gps = ser.readline()
    fichero.write(gps)
    '''
    if (gps.startswith('$GNRMC')):
        if(primera == True):
            primera = False
        else:
            fichero.close()
        print("$GNRMC")
        tiempoActual = datetime.now().strftime("%d%m%y_%H%M%S%f")
        nombreFichero = '/media/card/gps_'+ tiempoActual +'.txt'
        fichero = open(nombreFichero, "wb")
        fichero.write(gps)
    if (gps.startswith('$GNZDA')):
        fichero.write(gps)
    if (gps.startswith('$GNTXT')):
        #No hacer nada
        print("Empieza")
    '''
    #Mensaje que nos proporciona la posicion
    if(gps.startswith('$GNGGA')):
        GGA = gps.split(',')
        if(GGA[2]!= '' and GGA[3]!= ''):
            latitud = GGA[2]+","+GGA[3]
            longitud = GGA[4]+","+GGA[5]
            altitudMetros = toFloat(GGA[9])
            altitudGrados = toFloat(GGA[11])
            gps = {'latitud':latitud, 'longitud':longitud, "altitudmetros" : altitudMetros, "altitudgrados" : altitudGrados}
            posicion = json.dumps(gps)
            almacenamientoRedis.set('posicion', posicion)
        print(GGA)
    #Mensaje que nos proporciona el tiempo y fecha
    if(gps.startswith('$GNZDA')):
        ZDA = gps.split(',')
        if(ZDA[1]!= ''):
            UTC = ZDA[1]
            dia = ZDA[2]
            mes = ZDA[3]
            ano = ZDA[4]
            tiempo = {'UTC':UTC, 'dia':dia, 'mes':mes, 'ano':ano}
            almacenamientoRedis.set('tiempo', json.dumps(tiempo))
        else:
            almacenamientoRedis.set('tiempo', '')
    '''
    else:
        fichero.write(gps)
    '''


