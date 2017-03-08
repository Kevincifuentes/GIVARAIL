import numpy as n
import math as m

def ExtendedKF(y_k, P_k, F_k, Q_k, z_k, H_k, R_k):
    y_k = n.matrix([[y_k[0,0]], [y_k[1,0]], [y_k[2,0]]])
    a = n.zeros((3, 3), float)
    n.fill_diagonal(a, P_k[0])
    P_k = a
    b = n.zeros((3, 3), float)
    n.fill_diagonal(b, 1)
    F_k = b
    c = n.zeros((3, 3), float)
    n.fill_diagonal(c, Q_k[0])
    Q_k = c
    z_k = n.matrix([[z_k[0]], [z_k[1]], [z_k[2]]])
    H_k = n.asmatrix(H_k, float)
    d = n.zeros((3, 3), float)
    n.fill_diagonal(d, R_k[0])
    R_k = d

    #P_k = n.matrix([[P_k, 0, 0],[0,P_k,0],[0,0,P_k]])
    y_k = F_k * y_k
    skewmatrix = n.array([[0, -y_k[2], y_k[1]], [y_k[2], 0, -y_k[0]], [-y_k[1], y_k[0], 0]])
    #print((m.sin(n.linalg.norm(y_k))/n.linalg.norm(y_k))*skewmatrix)
#    print(((1-m.cos(n.linalg.norm(y_k)))/n.linalg.norm(y_k))*n.linalg.matrix_power(skewmatrix,2))
    C = n.identity(3) + (m.sin(n.linalg.norm(y_k))/n.linalg.norm(y_k))*skewmatrix+((1-m.cos(n.linalg.norm(y_k)))/m.pow(n.linalg.norm(y_k),2))*n.linalg.matrix_power(skewmatrix,2)
    H = n.transpose(C)*n.transpose([0,0,1])
    H = n.matrix([[H[0,2]],[H[1,2]],[H[2,2]]])
    P_k = F_k*P_k*n.transpose(F_k)+Q_k
    K = P_k*n.transpose(H_k) / (H_k*P_k*n.transpose(H_k)+R_k)
    K = n.dot(P_k*n.transpose(H_k), n.linalg.matrix_power((H_k*P_k*n.transpose(H_k)+R_k),-1))
    #print(K)
    y_k = y_k+K*(z_k-H)
    P_k = (n.identity(len(y_k)) - K*H_k)*P_k
    return y_k, P_k
