# -*- coding: utf-8 -*-
import csv
import numpy
from numpy.lib.function_base import append

import utm
import math as m
from ExtendedKF import *
from Jacobian import *

def rotationM(Acc, yaw):
    #Estimar la matriz de rotación a partir del valor de los Acc
    pitch = m.atan(-Acc[0] / m.sqrt(m.pow(Acc[1], 2)+ m.pow(Acc[2],2))) #Y
    roll = m.atan2(Acc[1], Acc[2]) #X

    C_b2n_initial = numpy.transpose([[m.cos(yaw)*m.cos(pitch), m.sin(yaw)*m.cos(pitch), -m.sin(pitch)],
                                     [m.cos(yaw)*m.sin(pitch)*m.sin(roll)-m.sin(yaw)*m.cos(roll), m.sin(yaw)*m.sin(pitch)*m.sin(roll)+
                                     m.cos(yaw)*m.cos(roll), m.cos(pitch)*m.sin(roll)],
                                     [m.cos(yaw)*m.sin(pitch)*m.cos(roll)+m.sin(yaw)*m.sin(roll), m.sin(yaw)*m.sin(pitch)*m.cos(roll)-
                                      m.cos(yaw)*m.sin(roll), m.cos(pitch)*m.cos(roll)]])

    angle = m.acos((numpy.trace(C_b2n_initial)-1)/2)

    axis = 1/ (2*m.sin(angle))*numpy.transpose([[C_b2n_initial[2,1]-C_b2n_initial[1,2]],
                                                [C_b2n_initial[0,2]-C_b2n_initial[2,0]],
                                                [C_b2n_initial[1,0]-C_b2n_initial[0,1]]])

    return axis

def rotm2eul(C_b2n):
    if C_b2n[2,0] != 1 and C_b2n[2,0] != -1:
        pitch1 = -m.asin(C_b2n[2,0])
        pitch2 = m.pi-pitch1

        roll1 = m.atan2(C_b2n[2,1]/m.cos(pitch1), C_b2n[2,2]/m.cos(pitch1))
        roll2 = m.atan2(C_b2n[2,1]/m.cos(pitch2), C_b2n[2,2]/m.cos(pitch2))

        psi1 = m.atan2(C_b2n[1,0]/m.cos(pitch1), C_b2n[0,0]/m.cos(pitch1))
        psi2 = m.atan2(C_b2n[1,0]/m.cos(pitch2), C_b2n[0,0]/m.cos(pitch2))

        eul = [roll1, pitch1, psi1]
    else:
        psi = m.atan2(C_b2n[1,0], C_b2n[0,0])
        if C_b2n[2,0] == -1:
            pitch = m.pi/2
            roll = psi+m.atan2(C_b2n[0,1], C_b2n[0,2])
        else:
            pitch = -m.pi/2
            roll = -psi+m.atan2(-C_b2n[0,1], -C_b2n[0,2])
        eul = [roll,pitch,psi]

    return eul

def EKF(y_k,P_k,F_k,Q_k,z_k,H_k,R_k):
    #print(y_k)
    #print(P_k)
    #print(F_k)
    #print(Q_k)
    z_k = numpy.transpose(numpy.matrix(z_k[0:4, 0]))
    #print(H_k)
    #print(R_k)
    y_k = F_k*y_k

    P_k = F_k*P_k*numpy.transpose(F_k)+Q_k
    #print(numpy.linalg.inv(H_k*P_k*numpy.transpose(H_k)+R_k))
    K = P_k*numpy.transpose(H_k)*numpy.linalg.inv(H_k*P_k*numpy.transpose(H_k)+R_k)
    #print(K)
    y_k = y_k+K*(z_k-H_k*y_k)
    P_k=(numpy.identity(len(y_k))-K*H_k)*P_k

    return y_k,P_k

def fuseIMU_GPS():
    numpy.set_printoptions(precision=20)
    #valoresPrueba_240117_175525457130_formatLatLng.csv
    input_var = raw_input("Introduce el nombre del fichero de entrada: ")

    #Inicializacion de variables
    window_size = 31 #tamano de ventana para media y varianza de aceleracion
    window_size_filter = 23 #tamano de ventana para el filtro de mediana

    #Numero de muestras (segundos * frecuencia)
    seconds = 200 # 100 hz y 2 segundos
    current =  seconds - (window_size-1)/2-(window_size_filter-1)/2

    gravity = 9.80665 #Valor en m/s^2 de gravedad

    reader = csv.reader(open(input_var, "rb"), delimiter=",")
    x = list(reader)
    data = numpy.array(x).astype("float64")
    rango = data[9:len(data)]

    #GNSS
    # Latitude: [deg]
    # Longitude: [deg]
    # Altitude: [m]
    # DOP: Nx3
    dataGNSS = rango[:,[0,1,2,16,17,18]]


    for i in xrange(len(dataGNSS)):
        if dataGNSS[i, 1] != 0:
            valorUTM = utm.from_latlon(dataGNSS[i,0], dataGNSS[i,1])
            dataGNSS[i,1] = valorUTM[0]
            dataGNSS[i,0] = valorUTM[1]

    ## IMU
    # Accelerometer: Nx3 [m/s2]
    # Gyroscope: Nx3 [rad/s]
    # Magnetometer: Nx3 [G]
    # EulerAngles: Yaw, Pitch, Roll [deg]
    # Pressure: Rx1 [Pa]
    dataIMU = rango[:,3:16]

    # de grados a radianes (yaw, pitch, roll)
    dataIMU[:, 9:12] = dataIMU[:, 9:12] * m.pi/180
    #presion de Pa a HPa
    dataIMU[:, 12] = dataIMU[:, 12]/100
    #para resolver valores de 0 en acc, gyro, mag, roll, pitch, yaw
    #print(dataIMU[0, 0:13])

    for i in range(1, len(dataIMU)):
        if dataIMU[i, 1] == 0:
            if dataIMU[i+1, 1] == 0:
                # dos consecutivos
                dataIMU[i, 0:13] = (dataIMU[i-1, 0:13] + dataIMU[i+2, 0:13]) /2
                if dataIMU[i+2,1] == 0:
                    # tres consecutivos
                    dataIMU[i, 0:13] = (dataIMU[i-1, 0:13] + dataIMU[i+3, 0:13]) /2
                    if dataIMU[i+3, 1] == 0:
                        print("4 consecutivos")
            else:
                dataIMU[i, 0:13] = (dataIMU[i-1, 0:13] + dataIMU[i+1, 0:13])/2

    #TimeStamp
    dataTime = rango[:,19]

    data = None

    a_b = numpy.zeros((seconds,3),'float64') #Vector de aceleracion
    w_b = numpy.zeros((seconds,3),'float64') #Vector de giroscopos
    b_b = numpy.zeros((seconds,3),'float64') #Vector de magnetometro
    p_b = numpy.zeros((1,len(rango))) #TODO: CHECK
    gnss = numpy.zeros((seconds, 3), 'float64')

    #Vector para estimacion de posicion
    r_n = numpy.ones((current, 3))
    for x in range(0, current):
        r_n[x, 0:3] = dataGNSS[0, [1,0,2]]

    v_n = numpy.zeros((3,1))
    Altura = r_n[0,2]

    # Estimamos con un KF la matriz de rotación inicial usando las 100 primeras muestras del acelerómetro

    # Vector de estado inicial
    yaw = -170*numpy.pi/180
    axis = rotationM(dataIMU[1,0:3]/m.sqrt(m.pow(dataIMU[1,0],2)+m.pow(dataIMU[1,1],2)+m.pow(dataIMU[1,2],2)),yaw)
    axis = numpy.matrix([[axis[0,0]],[axis[0,1]],[axis[0,2]]])
    #matriz de covarianza del estado
    P_ini = numpy.diag(0.01*numpy.ones((1,3), numpy.float64))
    #Matriz de covarianza del error en el modelo dinámico
    Q_ini = numpy.diag((0.01*m.pow(0.01,2)/2)*numpy.ones((1,3), numpy.float64))
    #Matriz de covarianza del error envaloresPrueba_240117_175525457130_formatLatLng.csv el modelo de mediciones
    R_ini = numpy.diag(0.01*numpy.ones((1,3), numpy.float64))

    for N in range(2,100):
       # H_ini = Jacobian(axis)
       #TODO: CHANGE IT USING FUNCTION
        H_ini = Jacobian(axis)
        [axis, P_ini] = ExtendedKF(axis, P_ini, numpy.diag(numpy.ones((1,3), numpy.float64)), Q_ini, numpy.transpose(dataIMU[N, 0:3])/
                                   m.sqrt(m.pow(dataIMU[1, 0], 2)+m.pow(dataIMU[1,1],2)+m.pow(dataIMU[1,2],2)), H_ini, R_ini)
        break
    #Obtenemos la matriz a partir del vector de rotación
    skewmatrix =  numpy.matrix([[0, -axis[2], axis[1]],[axis[2], 0, -axis[0]],[-axis[1], axis[0], 0]])
    C_b2n_inicial = numpy.identity(3)+(m.sin(numpy.linalg.norm(axis))/numpy.linalg.norm(axis))*skewmatrix+((1-m.cos(numpy.linalg.norm(axis)))/
                    numpy.linalg.norm(axis)**2)*skewmatrix**2
    C_b2n = C_b2n_inicial
    #C_b2n matriz 3x3

    ## Initial state vector (attitude, gyro, position, velocity and acceleration error vectors)
    dx = numpy.zeros((15,1))
    #Covariance matrix of the state.
    P = numpy.diag([0, 0, 0, 0.01, 0.01, 0.01, 0, 0, 0, 0, 0, 0, 0.01, 0.01, 0.01])

    Q = numpy.diag([0.0000018, 0.0000018, 0.0000018, 0, 0, 0, 0, 0, 0, 0.00003, 0.00003, 0.00003, 0, 0, 0])

    R = numpy.diag([10000, 10000, 10000, 10000]).astype(numpy.float64)

    m2 = numpy.zeros((4,4))

    H = numpy.matrix(([[0,0,0,0,0,0,1,0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,1,0,0,0,0,0,0,0],
         [0,0,0,0,0,0,0,0,1,0,0,0,0,0,0], [0,0,0,0,0,0,0,0,1,0,0,0,0,0,0]]))

    ##LOOP
    i_imu = 0
    i_gnss = 0
    i_baro = 0
    imu_rate = 100
    #Si no lo pongo así, me da error
    delta = 1.0e-02
    N = 0
    n = 0
    fusePosition_100Hz = []
    fuseAltura_50hz = []
    fusePosition_2Hz = []
    #Necesario dado que la posición ultima es seconds-1
    seconds_index = seconds -1
    #Necesario dado que la posición ultima es current-1
    current_index = current -1
    while N < len(dataGNSS[:,0]):
        if n < seconds:
            a_b[n,:] = dataIMU[N, 0:3]
            w_b[n,:] = dataIMU[N, 3:6]
            b_b[n,:] = dataIMU[N, 6:9]
            p_b[0,n] = dataIMU[N, 12]

            if p_b[0,n] != 0:
                p_b_ = p_b[0, n]
            n = n+1
        else:
            a_b[seconds_index,:] = dataIMU[N, 0:3]
            w_b[seconds_index,:] = dataIMU[N, 3:6]
            b_b[seconds_index,:] = dataIMU[N, 6:9]
            p_b[0, seconds_index] = dataIMU[N, 12]

            gnss[seconds_index,:] = dataGNSS[N, 0:3]

            i_imu = i_imu+1

            #Apply INS method
            w_b_ = w_b[current_index,:]-numpy.transpose(dx[3:6]) #Remove angular velocity error (body-frame)
            a_b_ = a_b[current_index,:]-numpy.transpose(dx[12:15]) #Remove aceleration error (body-frame)
            omega = numpy.matrix(([[0,-w_b_[0,2],w_b_[0,1]],[w_b_[0,2], 0, -w_b_[0,0]],[-w_b_[0,1], w_b_[0,0], 0]])) #Ske-symmetric matrix of w_b_ (body-frame)
            '''
                Update sensor orientation with respect to the navigation frame.
                For a small enough time instant omega==constant. Then
                C'(t)=omega*C(t), and its solution C=exp(omega*t)*C(t_0).
                Therefore, C(k-1)=exp(omega*delta)*C(k), and approximating
                exp(omega*delta) by Padé formula:
            '''
            #SOLUCIONADO: Cambiar división por pow -1
            C_b2n = numpy.dot(numpy.dot(C_b2n, (2*numpy.identity(3)+omega*delta)), numpy.linalg.matrix_power((2*numpy.identity(3)-omega*delta),-1))
            #a_n = C_b2n*a_b_'-[0; 0; gravity];
            #Obtain aceleration in the navigation frame and subtract the gravity
            #print(C_b2n)
            #print(numpy.transpose(a_b_))
            #print(C_b2n*numpy.transpose(a_b_))
            a_n = C_b2n*numpy.transpose(a_b_)-numpy.matrix(([[0],[0],[gravity]]))
            #Integrate the aceleration to obtain the velocity vector
            v_n_ = v_n+a_n*delta

            #Integrate the velocity to obtain the position vector and subtract
            #the error obtained with the EKF
            r_n[current_index,:] = r_n[current_index-1,:]+numpy.transpose(v_n_)*delta-numpy.transpose(dx[6:9])

            #Quitar el error obtenido con el EKF de la velocidad
            v_n = v_n_-dx[9:12]
            a_n_ = C_b2n*numpy.transpose(a_b_)

            #print(C_b2n)
            S = numpy.matrix(([[0, -a_n_[2], a_n_[1]], [a_n_[2], 0, -a_n_[0]], [-a_n_[1], a_n_[0], 0]]))
            F = numpy.bmat([[numpy.identity(3), delta*C_b2n, numpy.zeros((3,3)), numpy.zeros((3,3)), numpy.zeros((3,3))],
                            [numpy.zeros((3,3)), numpy.identity(3), numpy.zeros((3,3)), numpy.zeros((3,3)), numpy.zeros((3,3))],
                            [numpy.zeros((3,3)), numpy.zeros((3,3)), numpy.zeros((3,3)), delta*numpy.identity(3), (m.pow(delta,2)/2)*C_b2n],
                            [delta*S, numpy.zeros((3,3)), numpy.zeros((3,3)), numpy.identity(3), delta*C_b2n],
                            [numpy.zeros((3,3)), numpy.zeros((3,3)), numpy.zeros((3,3)), numpy.zeros((3,3)), numpy.identity(3)]])

            #A second attitude refinement is accomplished with the angles
            #errors (note that d_phi=domega/delta).
            dtheta = numpy.matrix(([[0, -dx[2], dx[1]], [dx[2], 0, -dx[0]],[-dx[1], dx[0], 0]]))

            #Since the change in orientation is with respect to the navigation-
            #frame, in this case, the exponential approximation premultiplies
            #the rotation matrix
            C_b2n = (numpy.dot((2*numpy.identity(3)+ dtheta), numpy.linalg.matrix_power((2*numpy.identity(3)-dtheta),-1)))*C_b2n

            #Inicializar todos los errores a zero, exceptuando el error en aceleracion y velocidad angular
            dx[0:3,:] = numpy.transpose(numpy.matrix([0,0,0]))
            dx[6:12] = numpy.zeros((6,1))

            #Guardando resultados en variable

            eul = rotm2eul(C_b2n)

            fusePosition_100Hz.append([r_n[current_index,0], r_n[current_index,1], r_n[current_index,2],
                                            m.sqrt(m.pow(v_n[0],2)+m.pow(v_n[1],2)+m.pow(v_n[2],2)),
                                            eul[0], eul[1], eul[2]])


            #Datos de Presión

            if p_b[0, current_index] != 0:
                #Corregir con datos de presión
                Delta_altura = (-288.15/0.0065)*(m.pow((p_b_/1013.25),(-0.0065*287/gravity))-m.pow((p_b[0,current_index]/1013.25),(-0.0065*287/gravity)))

                #[m] h(i)-h(i-1)
                p_b_ = p_b[0,current_index]
                Altura = Altura + Delta_altura
                #Medidas
                m2[3,0] = r_n[current_index,2] - Altura #Error en altura posicion
                #Covarianza
                R[3,3] = 1.0e-02
                #Guardando resultados en variable
                i_baro = i_baro+1
                fuseAltura_50hz.append([Altura, r_n[current_index,2], gnss[current_index,2]])
            else:
                #Medidas
                m2[3,0] = 0
                #Covarianza
                R[3,3] = 10000


            if gnss[current_index,0] != 0:
                #Corregir con datos GPS (N-E-A)
                #Medidas
                m2[0:3,1] = numpy.transpose(r_n[current_index, 0:3]-gnss[current_index,([2,1,3])])
                #Covarianza TODO: ASK
                R[0:3, 0:3] = [[0.01,0,0],[0,0.01,0],[0,0,1]]

                #Guardando resultado en variable
                i_gnss = i_gnss+1
                #print(C_b2n)
                eul = rotm2eul(C_b2n)
                #print(eul)
                fusePosition_2Hz.append([r_n[current_index,0], r_n[current_index,1], r_n[current_index,2],
                                         eul[0], eul[1], eul[2]])
            else:
                #Medidas
                m2[0,0] = 0
                m2[1,0] = 0
                m2[2,0] = 0
                #Covarianza
                R[0:3,0:3] = numpy.identity(3)*10000

            #*[1 0 0; 0 cos(roll) sin(roll); 0 -sin(roll) cos(roll)]*b_b(current,:)';
            #Datos del magnetometro
           # b_n = numpy.matrix([[m.cos(eul[1]), 0, -m.sin(eul[1])],
           #        [0,1,0],
           #        [-m.sin(eul[1]),0,m.cos(eul[1])]])*numpy.matrix([[1,0,0],
           #         [0,m.cos(eul[0]), m.sin(eul[0])], [0,-m.sin(eul[0]), m.cos(eul[0])]])*numpy.transpose(b_b[current_index,:])
            #Md(Bilbao) = 0°51' W  ± 0°20'  changing by  0°8' E per year
           # yaw_compass = -m.atan2(b_n[1], b_n[0])-(-(0+51/60)*m.pi/180)
           # m2[4,0] = yaw - yaw_compass
           # R[4,4] = 1e-1

            ##EKF con el vector de errores en medidas y la matriz Jacobiana (H)

            [dx, P] = EKF(dx,P,F,Q,m2,H,R)
            a_b[0:seconds_index-1,:] = a_b[1:seconds_index,:]
            w_b[0:seconds_index-1,:] = w_b[1:seconds_index,:]
            b_b[0:seconds_index-1,:] = b_b[1:seconds_index,:]
            p_b[0, 0:seconds_index-1] = p_b[0, 1:seconds_index]
            r_n[0:current_index-1,:] = r_n[1:current_index,:]
            gnss[0:seconds_index-1,:] = gnss[1:seconds_index,:]
        N = N+1
    ##Fin del While
    #Utilizar datos
    print("FIN")

if __name__ == "__main__":
    fuseIMU_GPS()
