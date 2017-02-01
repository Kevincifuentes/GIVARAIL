#!/usr/bin/env python

import serial
import sys
import math
import atexit
import redis
import logging
import json

class ExitHooks(object):
    def __init__(self):
        self.exit_code = None
        self.exception = None

    def hook(self):
        self._orig_exit = sys.exit
        sys.exit = self.exit
        sys.excepthook = self.exc_handler

    def exit(self, code=0):
        self.exit_code = code
        self._orig_exit(code)

    def exc_handler(self, exc_type, exc, *args):
        self.exception = exc

hooks = ExitHooks()
hooks.hook()

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

#logging.basicConfig(filename='logs/hiloGPS.log',format='HiloGPS - %(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logging.basicConfig(filename='/media/card/logs/hiloGPS.log',format='HiloGPS - %(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)

ser = serial.Serial()
ser.baudrate = 115200
ser.port = '/dev/ttyACM0'

global almacenamientoRedis
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
    if hooks.exit_code is not None:
        print("ERROR: Desechufa el GPS y Reinicia el proceso")
        logging.error("HiloGPS muerto por Sys.exit(%d)" % hooks.exit_code)
    elif hooks.exception is not None:
        print("ERROR: Desechufa el GPS y Reinicia el proceso")
        logging.error("HiloGPS muerto por Excepcion: %s" % hooks.exception)
        error = {'error': 'error'}
        try:
            almacenamientoRedis.lpush('cola_gps', json.dumps(error))
        except KeyboardInterrupt:
            print("Interupcion IMU al enviar error")
    else:
        logging.error("Muerte natural")
    print("Fin del HiloGPS")
    logging.info('HILOGPS terminado.')

atexit.register(finalizar)

ser.open()

if not ser.isOpen():
    print("HILOGPS: Unable to open serial port!")
    logging.error("No es posible abrir el serial para el GPS.")
    raise SystemExit

#Pone el baudrate a 115200 (NECESARIO PARA RECIBIR TODOS LOS MENSAJES)
ser.write("\xB5\x62\x06\x00\x14\x00\x01\x00\x00\x00\xD0\x08\x00\x00\x00\xC2")
ser.write("\x01\x00\x03\x00\x03\x00\x00\x00\x00\x00\xBC\x5E")

#Pone el GNSS a la frecuencia de 2hz
#ser.write("\xB5\x62\x06\x08\x06\x00\xF4\x01\x01\x00\x01\x00\x0B\x77")
#Pone el GNSS a la frecuencia de 1hz
ser.write("\xB5\x62\x06\x08\x06\x00\xE8\x03\x01\x00\x01\x00\x0B\x77")

ser.readline()

#Pone el GNSS en modo Automotive
ser.write("\xB5\x62\x06\x1A\x28\x00\x03\x00\x00\x00\x03\x04\x10\x02")
ser.write("\x50\xC3\x00\x00\x18\x14\x05\x3C\x00\x03\x00\x00\xFA\x00\xFA\x00\x64\x00\x2C\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x6C\x95")
ser.readline()
primera = True
global fichero
while True:
    try:
        gps = ser.readline()
    except KeyboardInterrupt:
        print("Lectura del GPS interrumpida.")
        logging.error("Lectura del GPS interrumpida")
        exit(0)
    except:
        logging.error("Error en el GPS. Mensaje: ", sys.exc_info()[0])

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

    if gps.startswith('$GNGGA') :
        GGA = gps.split(',')
        if GGA[2]!= '' and GGA[3]!= '' :
            latitud = GGA[2]
            ladoLatitud = GGA[3]
            longitud = GGA[4]
            ladoLongitud = GGA[5]
            fixValido = GGA[6]
            if fixValido == '0':
                print("ERROR: GPS devolviendo Fix Invalido")
                logging.error('ERROR: GPS devolviendo Fix Invalido')
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
                push_element = almacenamientoRedis.lpush('cola_gps', json.dumps(gps2))
                logging.info('Correcto enviado GPS')
        else:
            #print("ERROR: GPS devolviendo latitud y longitud vacia")
            logging.error('ERROR: GPS devolviendo latitud y longitud vacia')
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


