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
import numpy as np

def procesoExtra():
    variable = 10
    i = 0
    while i < 100:
        variable = variable * 16
        i = i+1
def cleanup():
     print '--------------------------------Limpiando----------------------------------------'
     os.killpg(PIDGPS, signal.SIGINT)
     os.killpg(PIDIMU, signal.SIGINT)



hiloGPS = subprocess.Popen([sys.executable, 'hiloGPS.py', '--username', 'root'])
hiloIMU = subprocess.Popen([sys.executable, 'hiloIMU.py', '--username', 'root'])
global PIDGPS
global PIDIMU
PIDGPS = os.getpgid(hiloGPS.pid)
PIDIMU = os.getpgid(hiloIMU.pid)
atexit.register(cleanup)
almacenamientoRedis = redis.StrictRedis(host='localhost', port=6379, db=0)
tiempoActual = datetime.datetime.now().strftime("%d%m%y_%H%M%S%f")
nombreFichero = '/media/card/valoresPrueba_'+ tiempoActual +'.txt'
fichero = open(nombreFichero, "wb")
contador = 0;
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
            barometro = str(posicionIMU["Barometro"])
            resultado = "";
            if contador == 100:
                contador = 0
                print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                timeStamp = datetime.datetime.now().strftime("%d-%m-%y %H:%M:%S.%f")
                resultado ="0,0,0,"+aceleracionX+","+aceleracionY+","+aceleracionZ+","+giroscopioX+","+giroscopioY+","+giroscopioZ+","+magnetometroX+","+magnetometroY+","+magnetometroZ+","+barometro+","+timeStamp+";\n"
                fichero.write(resultado)
            else:
                contador = contador +1
                resultado = "0,0,0,"+aceleracionX+","+aceleracionY+","+aceleracionZ+","+giroscopioX+","+giroscopioY+","+giroscopioZ+","+magnetometroX+","+magnetometroY+","+magnetometroZ+","+barometro+",0;\n"
                fichero.write(resultado)
            #print("Solo IMU:")
            #print(resultado)
        else:
            print("ERROR: No hay valores ni del GPS ni de la IMU.")
    else:
        posicionGPS = json.loads(posicion)
        if(valoresIMU == None):
            print("ERROR: No hay valores de la IMU.")
        else:
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
            barometro = str(posicionIMU["Barometro"])
            longitud = str(posicionGPS["longitud"])
            latitud = str(posicionGPS["latitud"])
            altitud = str(posicionGPS["altitudmetros"])
            procesoExtra()
            resultado = "";
            if contador == 100:
                print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                contador = 0
                timeStamp = datetime.datetime.now().strftime("%d-%m-%y %H:%M:%S.%f")
                resultado =latitud+","+longitud+","+altitud+","+aceleracionX+","+aceleracionY+","+aceleracionZ+","+giroscopioX+","+giroscopioY+","+giroscopioZ+","+magnetometroX+","+magnetometroY+","+magnetometroZ+","+barometro+","+timeStamp+";\n"
                fichero.write(resultado)
            else:
                contador = contador +1
                resultado = latitud+","+longitud+","+altitud+","+aceleracionX+","+aceleracionY+","+aceleracionZ+","+giroscopioX+","+giroscopioY+","+giroscopioZ+","+magnetometroX+","+magnetometroY+","+magnetometroZ+","+barometro+",0;\n"
                fichero.write(resultado)
            #print("Los dos:")
            #print(resultado)

        #>>>>>>>>>>>>>>>>>KALMAN con IMU y GPS
        #print("FILTRADO:"+str(posicionGPS))
        #print("FILTRADO:"+str(posicionIMU))
