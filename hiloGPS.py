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
        print("HILOGPS: Can't calculate from {0} side {1}".format(latlon, side))
        val = None
    return val

ser = serial.Serial()
ser.baudrate = 115200
ser.port = '/dev/ttyACM0'
almacenamientoRedis = redis.StrictRedis(host='localhost', port=6379, db=0)

def toFloat(value):
    val = None
    if value == None or value == '':
        return None
    try:
        val = float(value)
    except ValueError:
        print("Can't convert to float: {0}".format(value))
        val = None
    return val

def finalizar():
    print("HILOGPS: FIN")

atexit.register(finalizar)

ser.open()

if not ser.isOpen():
    print("HILOGPS: Unable to open serial port!")
    raise SystemExit

#Pone el baudrate a 115200 (NECESARIO PARA RECIBIR TODOS LOS MENSAJES)
ser.write("\xB5\x62\x06\x00\x14\x00\x01\x00\x00\x00\xD0\x08\x00\x00\x00\xC2")
ser.write("\x01\x00\x03\x00\x03\x00\x00\x00\x00\x00\xBC\x5E")

#Pone el GPS a la frecuencia de 2hz
ser.write("\xB5\x62\x06\x08\x06\x00\xF4\x01\x01\x00\x01\x00\x0B\x77")
ser.readline()
primera = True
global fichero
while True:
    gps = ser.readline()
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
    #print(gps)
    if(gps.startswith('$GNGGA')):
        GGA = gps.split(',')
        if(GGA[2]!= '' and GGA[3]!= ''):
            latitud = GGA[2]+","+GGA[3]
            longitud = GGA[4]+","+GGA[5]
            altitudMetros = toFloat(GGA[9])
            altitudGrados = toFloat(GGA[11])
            gps2 = {'latitud':latitud, 'longitud':longitud, "altitudmetros" : altitudMetros, "altitudgrados" : altitudGrados}
            push_element = almacenamientoRedis.lpush('cola_gps', json.dumps(gps2))
        #print("HILOGPS:"+ str(GGA))
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


