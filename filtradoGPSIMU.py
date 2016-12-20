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

def procesoExtra():
    variable = 10
    i = 0
    while i < 100:
        variable = variable * 16
        i = i+1

def cleanup():
     print '--------------------------------Limpiando----------------------------------------'
     try:
         os.killpg(PIDGPS, signal.SIGINT)
     except KeyboardInterrupt:
         print("Proceso GPS eliminado.")
     try:
         os.killpg(PIDIMU, signal.SIGINT)
     except KeyboardInterrupt:
         print("Proceso IMU eliminado.")
     print("Espere unos segundos...")
     subprocess.Popen([sys.executable, 'limpiarColaGPS.py', '--username', 'root'])
     subprocess.Popen([sys.executable, 'limpiarColaIMU.py', '--username', 'root'])

logging.basicConfig(filename='logs/logFiltradoGPSIMU.log',format='FiltradoGPSIMU - %(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)
hiloGPS = subprocess.Popen([sys.executable, 'hiloGPS.py', '--username', 'root'])
hiloIMU = subprocess.Popen([sys.executable, 'hiloIMU.py', '--username', 'root'])
time.sleep(8)
global PIDGPS
global PIDIMU
PIDGPS = os.getpgid(hiloGPS.pid)
PIDIMU = os.getpgid(hiloIMU.pid)

#stablish the method to run before exiting

atexit.register(cleanup)
#signal.signal(signal.SIGTERM, cleanup())

almacenamientoRedis = redis.StrictRedis(host='localhost', port=6379, db=0)
tiempoActual = datetime.datetime.now().strftime("%d%m%y_%H%M%S%f")
nombreFichero = '/media/card/valoresPrueba_'+ tiempoActual +'.txt'
fichero = open(nombreFichero, "wb")
contador = 0;
error = 0
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
                try:
                    #gnssN, gnssE, gnssU, accX, accY, accZ, gyrX, gyrY, gyrZ, magX, magY, magZ, bar, Fecha;
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
                    timeStamp = datetime.datetime.now().strftime("%d-%m-%y %H:%M:%S.%f")
                    resultado ="0,0,0,"+aceleracionX+","+aceleracionY+","+aceleracionZ+","+giroscopioX+","+giroscopioY+","+giroscopioZ+","+magnetometroX+","+magnetometroY+","+magnetometroZ+","+yaw+","+pitch+","+roll+","+barometro+","+timeStamp+";\n"
                    fichero.write(resultado)
                else:
                    contador = contador +1
                    resultado = "0,0,0,"+aceleracionX+","+aceleracionY+","+aceleracionZ+","+giroscopioX+","+giroscopioY+","+giroscopioZ+","+magnetometroX+","+magnetometroY+","+magnetometroZ+","+yaw+","+pitch+","+roll+","+barometro+",0;\n"
                    fichero.write(resultado)
                error = 0
                #print("Correcto enviando IMU")
                #logging.info('Correcto enviado IMU')
                #print("Solo IMU:")
                #print(resultado)
            else:
                #"ERROR: No hay valores ni del GPS ni de la IMU.")
                #print("Error no hay valores ni de la IMU, ni del GPS")
                if(error != 1):
                    logging.error("Error no hay valores ni de la IMU, ni del GPS")
                    error = 1


        else:
            posicionGPS = json.loads(posicion)
            if(valoresIMU == None):
                #"ERROR: No hay valores de la IMU.")
                print("Error no hay valores de la IMU")
                if(error != 2):
                    logging.error("Error no hay valores de la IMU")
                    error = 2
            else:
                try:
                    posicionIMU = json.loads(valoresIMU)
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
                except KeyError:
                    print("Error al obtener la informacion de GPS y IMU del objecto.")
                    logging.error('Error al obtener la informacion de GPS y IMU del objecto. Mensaje: '+ KeyError.message)


                procesoExtra()
                resultado = ""
                if contador == 100:
                    contador = 0
                    timeStamp = datetime.datetime.now().strftime("%d-%m-%y %H:%M:%S.%f")
                    resultado =latitud+","+longitud+","+altitud+","+aceleracionX+","+aceleracionY+","+aceleracionZ+","+giroscopioX+","+giroscopioY+","+giroscopioZ+","+magnetometroX+","+magnetometroY+","+magnetometroZ+","+yaw+","+pitch+","+roll+","+barometro+","+timeStamp+";\n"
                    fichero.write(resultado)
                else:
                    contador = contador +1
                    resultado = latitud+","+longitud+","+altitud+","+aceleracionX+","+aceleracionY+","+aceleracionZ+","+giroscopioX+","+giroscopioY+","+giroscopioZ+","+magnetometroX+","+magnetometroY+","+magnetometroZ+","+yaw+","+pitch+","+roll+","+barometro+",0;\n"
                    fichero.write(resultado)
                print("Correcto enviando IMU y GPS")
                logging.info('Correcto enviado IMU y GPS')
                error = 0
                #print("Los dos:")
                #print(resultado)

            #>>>>>>>>>>>>>>>>>KALMAN con IMU y GPS
            #print("FILTRADO:"+str(posicionGPS))
            #print("FILTRADO:"+str(posicionIMU))
except Exception:
    print("Error con el filtrado. Mensaje: "+ Exception.message)
    logging.error("Error con el filtrado. Mensaje: "+ Exception.message)
