#!/usr/bin/env python

import math
import atexit
import time
import redis
import json


almacenamientoRedis = redis.StrictRedis(host='localhost', port=6379, db=0)

while(True):

    posicion = almacenamientoRedis.get('posicion')
    posicionGPS = None
    if(posicion != None):
        posicionGPS = json.loads(posicion)

    valoresIMU = almacenamientoRedis.rpop('cola_imu')
    posicionIMU = None
    if(valoresIMU != None):
        posicionIMU = json.loads(valoresIMU)

    #Se obtiene de uno en uno o saco los cincuenta y proceso (¿?)
    #Habria que ejecutar el filtro de Kalman aqui
    print(str(posicionGPS))
    print(str(posicionIMU))

    if(posicion != 'None' and valoresIMU != 'None'):
        print("salir")
        break
