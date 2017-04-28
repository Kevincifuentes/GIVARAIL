#!/usr/bin/env python

import serial
import datetime
import math
import atexit
import redis
import json
import time

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
ser.baudrate = 115200
ser.port = '/dev/ttyACM0'
almacenamientoRedis = redis.StrictRedis(host='localhost', port=6379, db=0)

def toFloat( value):
    val = None
    val = float(value)
    return val

def finalizar():
    print("FIN")

atexit.register(finalizar)

ser.open()

if not ser.isOpen():
    print("Unable to open serial port!")
    raise SystemExit

#Pone el baudrate a 115200 (NECESARIO PARA RECIBIR TODOS LOS MENSAJES)
ser.write("\xB5\x62\x06\x00\x14\x00\x01\x00\x00\x00\xD0\x08\x00\x00\x00\xC2")
ser.write("\x01\x00\x03\x00\x03\x00\x00\x00\x00\x00\xBC\x5E")

#Pone el GNSS a la frecuencia de 2hz
#ser.write("\xB5\x62\x06\x08\x06\x00\xF4\x01\x01\x00\x01\x00\x0B\x77")
#Pone el GNSS a la frecuencia de 1hz
ser.write("\xB5\x62\x06\x08\x06\x00\xE8\x03\x01\x00\x01\x00\x0B\x77")
ser.readline()
global ficheroDatos
#fichero = open("/media/card/gpsPrueba.txt", "wb")
primera = True

while True:
    gps = ser.readline()
    #fichero.write(gps)
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
        if GGA[2]!= '' and GGA[3]!= '' :
            latitud = GGA[2]
            ladoLatitud = GGA[3]
            longitud = GGA[4]
            ladoLongitud = GGA[5]
            fixValido = GGA[6]
            if fixValido == '0':
                print("ERROR: GPS devolviendo Fix Invalido")
            else:
                altitudMetros = toFloat(GGA[9])
                altitudGrados = toFloat(GGA[11])
                while True:
                    gps = ser.readline()
                    if gps.startswith('$GNGSA'):
                        GSA = gps.split(',')
                        break
                while True:
                    gps = ser.readline()
                    if gps.startswith('$GNGST'):
                        GST = gps.split(',')
                        break
                while True:
                    gps = ser.readline()
                    if gps.startswith('$GNGBS'):
                        GBS = gps.split(',')
                        break
                standardDevLat = GST[6]
                standardDevLng = GST[7]
                standardDevAlt = GST[8]
                standardDevAlt = standardDevAlt[:standardDevAlt.find("*")]
                expectedErrorLat = GBS[2]
                expectedErrorLng = GBS[3]
                expectedErrorAlt = GBS[4]
                pdop = GSA[len(GSA)-3]
                hdop = GSA[len(GSA)-2]
                vdop = GSA[len(GSA)-1]
                vdop = vdop[:vdop.find("*")]
                gps2 = {'latitud':toDoubleLatLong(latitud, ladoLatitud), 'longitud':toDoubleLatLong(longitud, ladoLongitud), "altitudmetros" : altitudMetros, "altitudgrados" : altitudGrados, "HDOP": hdop, "VDOP": vdop, "PDOP" : pdop, "standardDevLat" : standardDevLat, "standardDevLng" : standardDevLng, "standardDevAlt": standardDevAlt, "expectedErrorLat" : expectedErrorLat, "expectedErrorLng" : expectedErrorLng, "expectedErrorAlt" : expectedErrorAlt}
                print(json.dumps(gps2))
                #print(datetime.datetime.now().strftime("%d-%m-%y %H:%M:%S.%f"))
                #push_element = almacenamientoRedis.lpush('cola_gps', json.dumps(gps2))
        #print(GGA)
    #Mensaje que nos proporciona el tiempo y fecha
    if(gps.startswith('$GNZDA')):
        ZDA = gps.split(',')
        #print(ZDA)
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


