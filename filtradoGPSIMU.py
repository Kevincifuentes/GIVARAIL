#!/usr/bin/env python

import math
import atexit
import time
import redis
import json
import numpy as np


almacenamientoRedis = redis.StrictRedis(host='localhost', port=6379, db=0)

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
        print("Los dos:")
        #>>>>>>>>>>>>>>>>>KALMAN con IMU y GPS
        #print("FILTRADO:"+str(posicionGPS))
        #print("FILTRADO:"+str(posicionIMU))
