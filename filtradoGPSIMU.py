#!/usr/bin/env python

import math
import atexit
import datetime
import redis
import json
import os
import signal
import time
import subprocess
import sys
import logging
import signal
import sys
import numpy as np

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

global almacenamientoRedis
almacenamientoRedis = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)

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

def procesoExtra():
    variable = 10
    i = 0
    while i < 100:
        variable = variable * 16
        i = i+1

def cleanup():
     #Para eliminar la ultima linea, dado que suele estar medio-escrita
     ficheroDatos.write("")
     ficheroDatos.close()
     try:
         f = open(nombreFichero, "r+")
         f.seek(-len(os.linesep), os.SEEK_END)
         f.write("")
         f.close()
     except Exception:
         logging.error("Error al normalizar fichero ")

     #print '--------------------------------Limpiando----------------------------------------'
     try:
         os.killpg(PIDGPS, signal.SIGINT)
     except KeyboardInterrupt:
         print("Proceso GPS eliminado.")
     try:
         os.killpg(PIDIMU, signal.SIGINT)
     except KeyboardInterrupt:
         print("Proceso IMU eliminado.")
     #print("Espere unos segundos...")
     if hooks.exit_code is not None:
        logging.error("filtradoGPSIMU muerto por Sys.exit(%d)" % hooks.exit_code)
     elif hooks.exception is not None:
        logging.error("filtradoGPSIMU muerto por Excepcion: %s" % hooks.exception)
     else:
        logging.error("Muerte natural")
     subprocess.Popen([sys.executable, '/GIVARAIL/limpiarColaGPS.py', '--username', 'root'])
     subprocess.Popen([sys.executable, '/GIVARAIL/limpiarColaIMU.py', '--username', 'root'])

     if hooks.exit_code is not None:
        print("filtradoGPSIMU muerto por Sys.exit(%d)" % hooks.exit_code)
        logging.error("filtradoGPSIMU muerto por Sys.exit(%d)" % hooks.exit_code)
     elif hooks.exception is not None:
        print("filtradoGPSIMU muerto por Excepcion: %s" % hooks.exception)
        logging.error("filtradoGPSIMU muerto por Excepcion: %s" % hooks.exception)
     else:
        logging.error("Muerte natural")

#logging.basicConfig(filename='logs/logFiltradoGPSIMU.log',format='FiltradoGPSIMU - %(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logging.basicConfig(filename='/media/card/logs/logFiltradoGPSIMU.log',format='FiltradoGPSIMU - %(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)
hiloGPS = subprocess.Popen([sys.executable, '/GIVARAIL/hiloGPS.py', '--username', 'root'])
hiloIMU = subprocess.Popen([sys.executable, '/GIVARAIL/hiloIMU.py', '--username', 'root'])
#time.sleep(15)

#Variables
PIDGPS = os.getpgid(hiloGPS.pid)
PIDIMU = os.getpgid(hiloIMU.pid)

#stablish the method to run before exiting

atexit.register(cleanup)
#signal.signal(signal.SIGTERM, cleanup())

tiempoActual = datetime.datetime.now().strftime("%d%m%y_%H%M%S%f")
global nombreFichero
nombreFichero = '/media/card/valoresPrueba_'+ tiempoActual +'.csv'
global ficheroDatos
ficheroDatos = open(nombreFichero, "wb")
contador = 0
error = 0

global aceleracionX
global aceleracionY
global aceleracionZ
global giroscopioX
global giroscopioY
global giroscopioZ
global magnetometroX
global magnetometroY
global magnetometroZ
global yaw
global pitch
global roll
global barometro

try:
    while(True):
        valoresIMU = almacenamientoRedis.rpop('cola_imu')
        posicionIMU = None

        posicion = almacenamientoRedis.rpop('cola_gps')
        posicionGPS = None
        if(posicion == None):
            #Esto quiere decir que no hay gps, se aplica KALMAN solo con la IMU
            if(valoresIMU != None):
                posicionIMU = json.loads(valoresIMU)
                #>>>>>>>>>>>>>>>>>KALMAN con IMU
                procesoExtra()

                #Comprobamos si el mensaje es de error del otro thread
                try:
                    error = posicionIMU["error"]
                    print("Se ha recibido error por parte del hiloIMU")
                    logging.error('Se ha recibido error por parte del hiloIMU')
                    sys.exit(1)
                except KeyError:
                    #Ok
                    error = 3

                try:
                    #gnssN,gnssE,gnssU,accX,accY,accZ,gyrX,gyrY,gyrZ,roll,pitch,yaw,magX,magY,magZ,bar,hdop,vdop,pdop,standardDevLat,standardDevLng,standardDevAlt,expectedErrorLat,expectedErrorLng,expectedErrorAlt,Fecha
                    aceleracionX = str(posicionIMU["Acceleration"]["accX"])
                    aceleracionY = str(posicionIMU["Acceleration"]["accY"])
                    aceleracionZ = str(posicionIMU["Acceleration"]["accZ"])
                    giroscopioX = str(posicionIMU["Angular Velocity"]["gyrX"])
                    giroscopioY = str(posicionIMU["Angular Velocity"]["gyrY"])
                    giroscopioZ = str(posicionIMU["Angular Velocity"]["gyrZ"])
                    magnetometroX = str(posicionIMU["Magnetic"]["magX"])
                    magnetometroY = str(posicionIMU["Magnetic"]["magY"])
                    magnetometroZ = str(posicionIMU["Magnetic"]["magZ"])
                    yaw = str(posicionIMU["Orientation Data"]["Yaw"])
                    pitch = str(posicionIMU["Orientation Data"]["Pitch"])
                    roll = str(posicionIMU["Orientation Data"]["Roll"])
                    barometro = str(posicionIMU["Barometro"])
                except KeyError:
                    print("Error al obtener la informacion de IMU. No se encuentra dicha clave en la coleccion")
                    logging.error('Error al obtener la informacion de IMU. Mensaje: '+ KeyError.message)

                resultado = "";
                if contador == 100:
                    contador = 0
                    #timeStamp = datetime.datetime.now().strftime("%d-%m-%y %H:%M:%S.%f")
                    then = datetime.datetime.now()
                    timeStamp = str(time.mktime(then.timetuple())*1e3 + then.microsecond/1e3)
                    resultado ="0,0,0,"+aceleracionX+","+aceleracionY+","+aceleracionZ+","+giroscopioX+","+giroscopioY+","+giroscopioZ+","+magnetometroX+","+magnetometroY+","+magnetometroZ+","+roll+","+pitch+","+yaw+","+barometro+",0,0,0,0,0,0,0,0,0,"+timeStamp+"\n"
                    ficheroDatos.write(resultado)
                else:
                    contador = contador +1
                    resultado = "0,0,0,"+aceleracionX+","+aceleracionY+","+aceleracionZ+","+giroscopioX+","+giroscopioY+","+giroscopioZ+","+magnetometroX+","+magnetometroY+","+magnetometroZ+","+roll+","+pitch+","+yaw+","+barometro+",0,0,0,0,0,0,0,0,0,0\n"
                    ficheroDatos.write(resultado)
                error = 0
                #print("Correcto enviando IMU")
                logging.info('Correcto enviado IMU')
                #print("Solo IMU:")
                #print(resultado)
            else:
                #"ERROR: No hay valores ni del GPS ni de la IMU.")
                #print("Error no hay valores ni de la IMU, ni del GPS")
                #logging.error("Error no hay valores ni de la IMU, ni del GPS")
                error = 1
                #print("Error no hay valores ni de la IMU ni del GNSS")
                logging.error("Error no hay valores ni de la IMU ni del GNSS")
                #exit(0)
        else:
            posicionGPS = json.loads(posicion)
            if(valoresIMU == None):
                #"ERROR: No hay valores de la IMU.")
                #Comprobamos si el mensaje es de error del thread
                #print("Error no hay valores de la IMU")
                try:
                    error = posicionGPS["error"]
                    print("Se ha recibido error por parte del hiloGPS")
                    logging.error('Se ha recibido error por parte del hiloGPS')
                    sys.exit(1)
                except KeyError:
                    #Ok
                    error = 3
                try:
                    longitud = str(posicionGPS["longitud"])
                    latitud = str(posicionGPS["latitud"])
                    altitud = str(posicionGPS["altitudmetros"])
                    hdop = str(posicionGPS["HDOP"])
                    vdop = str(posicionGPS["VDOP"])
                    pdop = str(posicionGPS["PDOP"])
                    standardDevLat = str(posicionGPS["standardDevLat"])
                    standardDevLng = str(posicionGPS["standardDevLng"])
                    standardDevAlt = str(posicionGPS["standardDevAlt"])
                    expectedErrorLat = str(posicionGPS["expectedErrorLat"])
                    expectedErrorLng = str(posicionGPS["expectedErrorLng"])
                    expectedErrorAlt = str(posicionGPS["expectedErrorAlt"])
                    #timeStamp = datetime.datetime.now().strftime("%d-%m-%y %H:%M:%S.%f")
                    then = datetime.datetime.now()
                    timeStamp = str(time.mktime(then.timetuple())*1e3 + then.microsecond/1e3)
                    resultado =latitud+","+longitud+","+altitud+","+aceleracionX+","+aceleracionY+","+aceleracionZ+","+giroscopioX+","+giroscopioY+","+giroscopioZ+","+magnetometroX+","+magnetometroY+","+magnetometroZ+","+roll+","+pitch+","+yaw+","+barometro+","+hdop+","+vdop+","+pdop+","+standardDevLat+","+standardDevLng+","+standardDevAlt+","+expectedErrorLat+","+expectedErrorLng+","+expectedErrorAlt+","+timeStamp+"\n"
                    ficheroDatos.write(resultado)
                except KeyError:
                    print("Error al obtener la informacion de GPS del objecto.")
                    logging.error('Error al obtener la informacion de GPS del objecto. Mensaje: '+ KeyError.message)

                if(error != 2):
                    logging.error("Error no hay valores de la IMU")
                    error = 2
            else:
                #Comprobamos si el mensaje es de error de los threads
                posicionIMU = json.loads(valoresIMU)
                try:
                    error = posicionGPS["error"]
                    print("Se ha recibido error por parte del hiloGPS")
                    logging.error('Se ha recibido error por parte del hiloGPS')
                    sys.exit(1)
                except KeyError:
                    #Ok
                    error = 3
                try:
                    error = posicionIMU["error"]
                    print("Se ha recibido error por parte del hiloIMU")
                    logging.error('Se ha recibido error por parte del hiloIMU')
                    sys.exit(1)
                except KeyError:
                    #Ok
                    error = 3

                try:
                    aceleracionX = str(posicionIMU["Acceleration"]["accX"])
                    aceleracionY = str(posicionIMU["Acceleration"]["accY"])
                    aceleracionZ = str(posicionIMU["Acceleration"]["accZ"])
                    giroscopioX = str(posicionIMU["Angular Velocity"]["gyrX"])
                    giroscopioY = str(posicionIMU["Angular Velocity"]["gyrY"])
                    giroscopioZ = str(posicionIMU["Angular Velocity"]["gyrZ"])
                    magnetometroX = str(posicionIMU["Magnetic"]["magX"])
                    magnetometroY = str(posicionIMU["Magnetic"]["magY"])
                    magnetometroZ = str(posicionIMU["Magnetic"]["magZ"])
                    yaw = str(posicionIMU["Orientation Data"]["Yaw"])
                    pitch = str(posicionIMU["Orientation Data"]["Pitch"])
                    roll = str(posicionIMU["Orientation Data"]["Roll"])
                    barometro = str(posicionIMU["Barometro"])
                    longitud = str(posicionGPS["longitud"])
                    latitud = str(posicionGPS["latitud"])
                    altitud = str(posicionGPS["altitudmetros"])
                    hdop = str(posicionGPS["HDOP"])
                    vdop = str(posicionGPS["VDOP"])
                    pdop = str(posicionGPS["PDOP"])
                    standardDevLat = str(posicionGPS["standardDevLat"])
                    standardDevLng = str(posicionGPS["standardDevLng"])
                    standardDevAlt = str(posicionGPS["standardDevAlt"])
                    expectedErrorLat = str(posicionGPS["expectedErrorLat"])
                    expectedErrorLng = str(posicionGPS["expectedErrorLng"])
                    expectedErrorAlt = str(posicionGPS["expectedErrorAlt"])
                except KeyError:
                    print("Error al obtener la informacion de GPS y IMU del objecto.")
                    logging.error('Error al obtener la informacion de GPS y IMU del objecto. Mensaje: '+ KeyError.message)


                ## TODO: REALIZAR FILTRADO EKF/UKF

                ## Mapmatching

                resultado = ""
                #timeStamp = datetime.datetime.now().strftime("%d-%m-%y %H:%M:%S.%f")
                then = datetime.datetime.now()
                timeStamp = str(time.mktime(then.timetuple())*1e3 + then.microsecond/1e3)
                latitud = toDoubleLatLong(latitud, "N")
                longitud = toDoubleLatLong(longitud, "W")
                resultado =latitud+","+longitud+","+altitud+","+aceleracionX+","+aceleracionY+","+aceleracionZ+","+giroscopioX+","+giroscopioY+","+giroscopioZ+","+magnetometroX+","+magnetometroY+","+magnetometroZ+","+roll+","+pitch+","+yaw+","+barometro+","+hdop+","+vdop+","+pdop+","+standardDevLat+","+standardDevLng+","+standardDevAlt+","+expectedErrorLat+","+expectedErrorLng+","+expectedErrorAlt+","+timeStamp+"\n"
                ficheroDatos.write(resultado)
                print("Correcto enviando IMU y GPS")
                logging.info('Correcto enviado IMU y GPS')
                error = 0
                #print("Los dos:")
                #print(resultado)

            #>>>>>>>>>>>>>>>>>KALMAN con IMU y GPS
            #print("FILTRADO:"+str(posicionGPS))
            #print("FILTRADO:"+str(posicionIMU))
except KeyboardInterrupt:
    print("Error con el filtrado.")
    logging.error("Error con el filtrado.")
    sys.exit(1)

