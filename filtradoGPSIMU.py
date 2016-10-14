#!/usr/bin/env python

import math
import atexit
import datetime
import redis
import json
import numpy as np

def procesoExtra():
    variable = 10
    i = 0
    while i < 10000:
        variable = variable * 16
        i = i+1


almacenamientoRedis = redis.StrictRedis(host='localhost', port=6379, db=0)
tiempoActual = datetime.now().strftime("%d%m%y_%H%M%S%f")
nombreFichero = '/media/card/valoresPrueba_'+ tiempoActual +'.txt'
fichero = open(nombreFichero, "wb")
contador = 0;
while(True):
    contador = contador + 1
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
            aceleracionX = posicionIMU["Acceleration"]["accX"]
            aceleracionY = posicionIMU["Acceleration"]["accY"]
            aceleracionZ = posicionIMU["Acceleration"]["accZ"]
            giroscopioX = posicionIMU["Angular Velocity"]["gyrX"]
            giroscopioY = posicionIMU["Angular Velocity"]["gyrY"]
            giroscopioZ = posicionIMU["Angular Velocity"]["gyrZ"]
            magnetometroX = posicionIMU["Magnetic"]["magX"]
            magnetometroY = posicionIMU["Magnetic"]["magY"]
            magnetometroZ = posicionIMU["Magnetic"]["magZ"]
            barometro = posicionIMU["Pressure"]

            if contador == 100:
                contador = 0
                fichero.write("0,0,0,"+aceleracionX+","+aceleracionY+","+aceleracionZ+","+giroscopioX+","+giroscopioY+","+giroscopioZ+","+magnetometroX+","+magnetometroY+","+magnetometroZ+","+barometro+",0;\n")
            else:
                fichero.write("0,0,0,"+aceleracionX+","+aceleracionY+","+aceleracionZ+","+giroscopioX+","+giroscopioY+","+giroscopioZ+","+magnetometroX+","+magnetometroY+","+magnetometroZ+","+barometro+","+";\n")
            print("Solo IMU:")
            #print("FILTRADO:"+str(posicionIMU))
        else:
            print("ERROR: No hay valores ni del GPS ni de la IMU.")
    else:
        posicionGPS = json.loads(posicion)
        if(valoresIMU == None):
            print("ERROR: No hay valores de la IMU. Cerrando...")
            exit(0)
        posicionIMU = json.loads(valoresIMU)

        aceleracionX = posicionIMU["Acceleration"]["accX"]
        aceleracionY = posicionIMU["Acceleration"]["accY"]
        aceleracionZ = posicionIMU["Acceleration"]["accZ"]
        giroscopioX = posicionIMU["Angular Velocity"]["gyrX"]
        giroscopioY = posicionIMU["Angular Velocity"]["gyrY"]
        giroscopioZ = posicionIMU["Angular Velocity"]["gyrZ"]
        magnetometroX = posicionIMU["Magnetic"]["magX"]
        magnetometroY = posicionIMU["Magnetic"]["magY"]
        magnetometroZ = posicionIMU["Magnetic"]["magZ"]
        barometro = posicionIMU["Pressure"]
        print("Los dos:")

        #>>>>>>>>>>>>>>>>>KALMAN con IMU y GPS
        #print("FILTRADO:"+str(posicionGPS))
        #print("FILTRADO:"+str(posicionIMU))
