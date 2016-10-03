#!/usr/bin/env python

import math
import atexit
import time
import redis
import json
from numpy import dot, sum, tile, linalg, exp, log, pi
from numpy.linalg import inv, det

def kf_predict(X, P, A, Q, B, U):
    X = dot(A, X) + dot(B, U)
    P = dot(A, dot(P, A.T)) + Q
    return(X,P)

def kf_update(X, P, Y, H, R):
    IM = dot(H, X)
    IS = R + dot(H, dot(P, H.T))
    K = dot(P, dot(H.T, inv(IS)))
    X = X + dot(K, (Y-IM))
    P = P - dot(K, dot(IS, K.T))
    LH = gauss_pdf(Y, IM, IS)
    return (X,P,K,IM,IS,LH)

def gauss_pdf(X, M, S):
    if M.shape()[1] == 1:
        DX = X - tile(M, X.shape()[1])
        E = 0.5 * sum(DX * (dot(inv(S), DX)), axis=0)
        E = E + 0.5 * M.shape()[0] * log(2 * pi) + 0.5 * log(det(S))
        P = exp(-E)
    elif X.shape()[1] == 1:
        DX = tile(X, M.shape()[1])- M
        E = 0.5 * sum(DX * (dot(inv(S), DX)), axis=0)
        E = E + 0.5 * M.shape()[0] * log(2 * pi) + 0.5 * log(det(S))
        P = exp(-E)
    else:
        DX = X-M
        E = 0.5 * dot(DX.T, dot(inv(S), DX))
        E = E + 0.5 * M.shape()[0] * log(2 * pi) + 0.5 * log(det(S))
        P = exp(-E)
    return (P[0],E[0])

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
