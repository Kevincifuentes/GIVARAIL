#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math
import warnings
import operator
import sys
from math import radians, cos, sin, asin, sqrt
from segmento import Segmento, Nodo
import utm
from scipy.spatial import distance as dist
import numpy

def dentroDeArea(checkPoint, centerPoint, km):
    ky = 40000 / 360;
    kx = math.cos(math.pi * centerPoint.lat / 180.0) * ky;
    dx = math.fabs(centerPoint.lng - checkPoint.lng) * kx;
    dy = math.fabs(centerPoint.lat - checkPoint.lat) * ky;
    return math.sqrt(dx * dx + dy * dy) <= km;

def index_by_id(lst, o):
    for i, item in enumerate(lst):
        if item is o:
            return i
    raise ValueError, "%s not in list" % o

def PolyArea(x,y):
    #Calcula el area del poligono que forman los puntos
    return 0.5*numpy.abs(numpy.dot(x,numpy.roll(y,1))-numpy.dot(y,numpy.roll(x,1)))

def order_points(pts):
    #Ordena los puntos en el sentido de las agujas del reloj
    # sort the points based on their x-coordinates
    xSorted = pts[numpy.argsort(pts[:, 0]), :]

    # grab the left-most and right-most points from the sorted
    # x-roodinate points
    leftMost = xSorted[:2, :]
    rightMost = xSorted[2:, :]

    # now, sort the left-most coordinates according to their
    # y-coordinates so we can grab the top-left and bottom-left
    # points, respectively
    leftMost = leftMost[numpy.argsort(leftMost[:, 1]), :]
    (tl, bl) = leftMost

    # now that we have the top-left coordinate, use it as an
    # anchor to calculate the Euclidean distance between the
    # top-left and right-most points; by the Pythagorean
    # theorem, the point with the largest distance will be
    # our bottom-right point
    D = dist.cdist(tl[numpy.newaxis], rightMost, "euclidean")[0]
    (br, tr) = rightMost[numpy.argsort(D)[::-1], :]

    # return the coordinates in top-left, top-right,
    # bottom-right, and bottom-left order
    return numpy.array([tl, tr, br, bl], dtype="float32")

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

def puntoApunto(listaPlanimetria, listaMedidas):
    """
    Funcion que calcula la traza mejorada utilizando la tecnica punto a punto
    """
    trazaMejorada = []
    numeroPuntosTotales = len(listaMedidas)
    contador = 1
    for nodo in listaMedidas:
        #Para cada uno de los nodos medidos calculo la distancia
        #a cada punto del plano
        print("("+str(contador)+"/"+str(numeroPuntosTotales)+")")
        valorNodo = utm.from_latlon(nodo.lat, nodo.lng)
        distancias = []

        for nodoPlano in listaPlanimetria:
            valorNodoPlano = utm.from_latlon(nodoPlano.lat, nodoPlano.lng)
            a = numpy.array((valorNodo[0], valorNodo[1]))
            b = numpy.array((valorNodoPlano[0], valorNodoPlano[1]))
            distanciaCalculada = numpy.linalg.norm(a-b)
            #distanciaCalculada = haversine(nodo.lng, nodo.lat, nodoPlano.lng, nodoPlano.lat)
            distancias.append(distanciaCalculada)
        #Despues se obtiene el punto con menor distancia, en teoria,
        #el más preciso
        contador = contador + 1
        min_index, min_value = min(enumerate(distancias), key=operator.itemgetter(1))
        trazaMejorada.append(listaPlanimetria[min_index])

    return trazaMejorada

def puntoApuntoArea(listaPlanimetria, listaMedidas, km):
    """
    Funcion que calcula la traza mejorada utilizando la tecnica punto a punto sobre los puntos alrededor en un area de x km
    """
    trazaMejorada = []
    numeroPuntosTotales = len(listaMedidas)
    contador = 1
    for nodo in listaMedidas:
        #Para cada uno de los nodos medidos calculo la distancia
        #a cada punto del plano
        print("("+str(contador)+"/"+str(numeroPuntosTotales)+")")
        valorNodo = utm.from_latlon(nodo.lat, nodo.lng)
        distancias = []
        listaPlanimetriaEnArea = []

        #Miro los nodos que estén en el area de alrededor (radio de 50 metros)
        for nodoPlano in listaPlanimetria:
            if dentroDeArea(nodoPlano, nodo, km) == True:
                listaPlanimetriaEnArea.append(nodoPlano)

        for nodoPlano in listaPlanimetriaEnArea:
            valorNodoPlano = utm.from_latlon(nodoPlano.lat, nodoPlano.lng)
            a = numpy.array((valorNodo[0], valorNodo[1]))
            b = numpy.array((valorNodoPlano[0], valorNodoPlano[1]))
            distanciaCalculada = numpy.linalg.norm(a-b)
            #distanciaCalculada = haversine(nodo.lng, nodo.lat, nodoPlano.lng, nodoPlano.lat)
            distancias.append(distanciaCalculada)
        #Despues se obtiene el punto con menor distancia, en teoria,
        #el más preciso
        contador = contador + 1
        min_index, min_value = min(enumerate(distancias), key=operator.itemgetter(1))
        trazaMejorada.append(listaPlanimetriaEnArea[min_index])
    return trazaMejorada

def puntoACurva(listaPlanimetria, segmentos, listaMedidas):
    """
    Funcion que calcula la traza mejorada utilizando la tecnica punto a curva
    """
    trazaMejorada = []
    numeroPuntosTotales = len(listaMedidas)
    contador = 1
    for i in xrange(len(listaMedidas)):
        #Para cada punto del camino se comprueba la distancia con cada segmento
        #y se coge el segmento con menor distancia
        print("("+str(contador)+"/"+str(numeroPuntosTotales)+")")
        contador = contador +1

        nodo = listaMedidas[i]
        valorNodoReal = utm.from_latlon(nodo.lat, nodo.lng)
        nodoReal = numpy.array((valorNodoReal[0] ,valorNodoReal[1]))

        t_calc = [None] * len(segmentos)
        d = [None] * len(segmentos)
        for j in xrange(len(segmentos)):
            #Obtengo los puntos del segmento
            nodoA = segmentos[j].nodoA
            nodoB = segmentos[j].nodoB
            valorNodoA = utm.from_latlon(nodoA.lat, nodoA.lng)
            valorNodoB = utm.from_latlon(nodoB.lat, nodoB.lng)
            A = numpy.array((valorNodoA[0] ,valorNodoA[1]))
            B = numpy.array((valorNodoB[0] ,valorNodoB[1]))

            #Calculo el vector director del segmento
            D = numpy.subtract(B, A)

            #Calculamos t' de la proyeccion
            normD = numpy.linalg.norm(D)
            t_calc[j] = numpy.divide(numpy.dot(numpy.subtract(nodoReal, A), numpy.transpose(D)), numpy.dot(normD,normD))

            if t_calc[j] < 0:
                d[j] = numpy.linalg.norm(numpy.subtract(nodoReal, A))
            elif t_calc[j] > 1:
                d[j] = numpy.linalg.norm(numpy.subtract(nodoReal, B))
            else:
                pprima = A + numpy.dot(t_calc[j], D)
                d[j] = numpy.linalg.norm(numpy.subtract(pprima, nodoReal))

        #Obtengo el mínimo de todos ellos
        j, min_value = min(enumerate(d), key=operator.itemgetter(1))

        nodoA = segmentos[j].nodoA
        nodoB = segmentos[j].nodoB
        valorNodoA = utm.from_latlon(nodoA.lat, nodoA.lng)
        valorNodoB = utm.from_latlon(nodoB.lat, nodoB.lng)
        A = numpy.array((valorNodoA[0] ,valorNodoA[1]))
        B = numpy.array((valorNodoB[0] ,valorNodoB[1]))
        D = numpy.subtract(B, A)

        #Tengo que convertirlos de nuevo a lat/lng
        #easting, northing, zone_number, zone_letter
        if t_calc[j] < 0:
            trazaMejorada.append(nodoA)
        elif t_calc[j] > 1:
            trazaMejorada.append(nodoB)
        else:
            pprima = A + numpy.dot(t_calc[j], D)
            pprimaTrans = numpy.transpose(pprima)
            #print(utm.to_latlon(pprimaTrans[0], pprimaTrans[1], valorNodoA[2], valorNodoA[3]))
            conversion = utm.to_latlon(pprimaTrans[0], pprimaTrans[1], valorNodoA[2], valorNodoA[3])
            #print(conversion[0])
            trazaMejorada.append(Nodo(conversion[0], conversion[1]))
    return trazaMejorada


def puntoACurvaArea(listaPlanimetria, segmentos, listaMedidas, km):
    """
    Funcion que calcula la traza mejorada utilizando la tecnica punto a curva con los puntos que estén en el area de alrededor con distancia de x
    """
    warnings.filterwarnings('error')
    trazaMejorada = []
    numeroPuntosTotales = len(listaMedidas)
    contador = 1
    for i in xrange(len(listaMedidas)):
        #Para cada punto del camino se comprueba la distancia con cada segmento
        #y se coge el segmento con menor distancia
        print("("+str(contador)+"/"+str(numeroPuntosTotales)+")")
        contador = contador +1

        nodo = listaMedidas[i]
        valorNodoReal = utm.from_latlon(nodo.lat, nodo.lng)
        nodoReal = numpy.array((valorNodoReal[0] ,valorNodoReal[1]))

        #Miramos los segmentos que estén dentro del area
        listaSegmentosArea = []
        for segmento in segmentos:
            if dentroDeArea(segmento.nodoA, nodo, km) == True or dentroDeArea(segmento.nodoB, nodo, km) == True:
                listaSegmentosArea.append(segmento)

        t_calc = [None] * len(listaSegmentosArea)
        d = [None] * len(listaSegmentosArea)
        for j in xrange(len(listaSegmentosArea)):
            #Obtengo los puntos del segmento
            nodoA = listaSegmentosArea[j].nodoA
            nodoB = listaSegmentosArea[j].nodoB
            valorNodoA = utm.from_latlon(nodoA.lat, nodoA.lng)
            valorNodoB = utm.from_latlon(nodoB.lat, nodoB.lng)
            A = numpy.array((valorNodoA[0] ,valorNodoA[1]))
            B = numpy.array((valorNodoB[0] ,valorNodoB[1]))

            #Calculo el vector director del segmento
            D = numpy.subtract(B, A)

            #Calculamos t' de la proyeccion
            normD = numpy.linalg.norm(D)
            try:
                t_calc[j] = numpy.divide(numpy.dot(numpy.subtract(nodoReal, A), numpy.transpose(D)), numpy.dot(normD,normD))
            except RuntimeWarning:
                d[j] = sys.maxint
                continue

            if t_calc[j] < 0:
                d[j] = numpy.linalg.norm(numpy.subtract(nodoReal, A))
            elif t_calc[j] > 1:
                d[j] = numpy.linalg.norm(numpy.subtract(nodoReal, B))
            else:
                pprima = A + numpy.dot(t_calc[j], D)
                d[j] = numpy.linalg.norm(numpy.subtract(pprima, nodoReal))

        #Obtengo el mínimo de todos ellos
        j, min_value = min(enumerate(d), key=operator.itemgetter(1))

        nodoA = listaSegmentosArea[j].nodoA
        nodoB = listaSegmentosArea[j].nodoB
        valorNodoA = utm.from_latlon(nodoA.lat, nodoA.lng)
        valorNodoB = utm.from_latlon(nodoB.lat, nodoB.lng)
        A = numpy.array((valorNodoA[0] ,valorNodoA[1]))
        B = numpy.array((valorNodoB[0] ,valorNodoB[1]))
        D = numpy.subtract(B, A)

        #Tengo que convertirlos de nuevo a lat/lng
        #easting, northing, zone_number, zone_letter
        if t_calc[j] < 0:
            trazaMejorada.append(nodoA)
        elif t_calc[j] > 1:
            trazaMejorada.append(nodoB)
        else:
            pprima = A + numpy.dot(t_calc[j], D)
            pprimaTrans = numpy.transpose(pprima)
            #print(utm.to_latlon(pprimaTrans[0], pprimaTrans[1], valorNodoA[2], valorNodoA[3]))
            conversion = utm.to_latlon(pprimaTrans[0], pprimaTrans[1], valorNodoA[2], valorNodoA[3])
            #print(conversion[0])
            trazaMejorada.append(Nodo(conversion[0], conversion[1]))
    return trazaMejorada


def curvaACurva(listaPlanimetria, segmentos, listaMedidas):
    """
    Funcion que calcula la traza mejorada utilizando la tecnica curva a curva
    """
    num_min_candidatos = 2
    trazaMejorada = []
    #Para el primer punto, tecnica punto a curva
    unosolo = []
    unosolo.append(listaMedidas[0])
    trazaMejorada.append(puntoACurva(listaPlanimetria, segmentos, unosolo)[0])
    i = 1
    numeroPuntosTotales = len(listaMedidas)
    while i < len(listaMedidas):
        print("("+str(i)+"/"+str(numeroPuntosTotales)+")")
        #Elegir segmentos candidatos utilizando punto a punto
        #Calcular distancia a todos los puntos
        nodo = listaMedidas[i]
        valorNodo = utm.from_latlon(nodo.lat, nodo.lng)
        dist = []
        for nodoPlano in listaPlanimetria:
            valorNodoPlano = utm.from_latlon(nodoPlano.lat, nodoPlano.lng)
            a = numpy.array((valorNodo[0], valorNodo[1]))
            b = numpy.array((valorNodoPlano[0], valorNodoPlano[1]))
            distanciaCalculada = numpy.linalg.norm(a-b)

            #distanciaCalculada = haversine(nodo.lng, nodo.lat, nodoPlano.lng, nodoPlano.lat)
            dist.append(distanciaCalculada)

        #Obtengo el los indices sobre el array inicial de los valores ordenados
        dist_ord = numpy.sort(dist)
        indices = numpy.argsort(dist)

        dist = []

        #numero de candidatos
        num_candidatos = 1
        #numero de nodos comprobados
        n_nodo = 0
        candidates = []

        #Seguimos hasta alcanzar el numero minimo de candidatos
        while num_candidatos < num_min_candidatos and n_nodo < (len(listaPlanimetria))+1:
           j=0
           #buscamos segmentos que tienen por extremo el nodo mas cercano
           while j < len(segmentos) and num_candidatos < num_min_candidatos+1:
               indexNodoA = index_by_id(listaPlanimetria, segmentos[j].nodoA)
               indexNodoB = index_by_id(listaPlanimetria, segmentos[j].nodoB)
               if indexNodoA == indices[n_nodo] or indexNodoB == indices[n_nodo] and len(numpy.where(candidates == j))==0:
                   candidates.append(j)
                   num_candidatos= num_candidatos +1
               j=j+1
           n_nodo = n_nodo+1

        #Calcular la longitud del segmento actual
        valorSegmentoA = utm.from_latlon(nodo.lat, nodo.lng)
        valorSegmentoB = utm.from_latlon(listaMedidas[i-1].lat, listaMedidas[i-1].lng)
        a = numpy.array((valorSegmentoA[0], valorSegmentoA[1]))
        b = numpy.array((valorSegmentoB[0], valorSegmentoB[1]))
        long_actual = numpy.linalg.norm(a-b)
        if long_actual == 0.0:
            print("0")
            trazaMejorada.append(trazaMejorada[i-1])
        else:
            areas = []
            for k in xrange(len(candidates)):
                #Calcular area entre el segmento actual y el segmento candidato

                #Vertices del poligono
                X = []
                valorNodoAnterior = utm.from_latlon(listaMedidas[i-1].lat, listaMedidas[i-1].lng)
                valorNodoActual = valorNodo
                valorNodoA = utm.from_latlon(segmentos[candidates[k]].nodoA.lat, segmentos[candidates[k]].nodoA.lng)
                valorNodoB = utm.from_latlon(segmentos[candidates[k]].nodoB.lat, segmentos[candidates[k]].nodoB.lng)
                puntos = numpy.array([[valorNodoAnterior[0], valorNodoAnterior[1]], [valorNodoActual[0], valorNodoActual[1]], [valorNodoA[0], valorNodoA[1]], [valorNodoB[0], valorNodoB[1]]], dtype="float32")
                #ordeno los puntos en el sentido de las agujas del reloj
                puntosOrdenados = order_points(puntos)
                #calculo el area del poligono
                #print(puntosOrdenados)
                #print(puntosOrdenados[:,0])
                #print(puntosOrdenados[:,1])
                poly = PolyArea(puntosOrdenados[:,0], puntosOrdenados[:,1])
                #print(poly)
                areas.append(poly)
                dist.append(poly / long_actual)

            min_index, min_value = min(enumerate(dist), key=operator.itemgetter(1))
            areas = []
            dist = []

            #Corrijo el punto con la tecnica punto a curva sobre el segmento
            segmento_seleccionado = segmentos[candidates[min_index]]
            candidates = []

            nodoA = segmento_seleccionado.nodoA
            nodoB = segmento_seleccionado.nodoB
            valorNodoA = utm.from_latlon(nodoA.lat, nodoA.lng)
            valorNodoB = utm.from_latlon(nodoB.lat, nodoB.lng)
            A = numpy.array((valorNodoA[0] ,valorNodoA[1]))
            B = numpy.array((valorNodoB[0] ,valorNodoB[1]))

            #Calculo el vector director del segmento
            D = numpy.subtract(B, A)
            P = numpy.array((valorNodo[0], valorNodo[1]))

            #Calculamos t' de la proyeccion
            normD = numpy.linalg.norm(D)
            t_calc = numpy.divide(numpy.dot(numpy.subtract(P, A), numpy.transpose(D)), numpy.dot(normD,normD))

            if t_calc < 0:
                trazaMejorada.append(nodoA)
                #print(nodoA)
            elif t_calc > 1:
                #print(nodoB)
                trazaMejorada.append(nodoB)
            else:
                pprima = A + numpy.dot(t_calc, D)
                pprimaTrans = numpy.transpose(pprima)
                conversion = utm.to_latlon(pprimaTrans[0], pprimaTrans[1], valorNodoA[2], valorNodoA[3])
                #print(conversion)
                trazaMejorada.append(Nodo(conversion[0], conversion[1]))
        i = i+1
    return trazaMejorada


def curvaACurvaArea(listaPlanimetria, segmentos, listaMedidas, km):
    """
    Funcion que calcula la traza mejorada utilizando la tecnica curva a curva
    """
    num_min_candidatos = 2
    trazaMejorada = []
    #Para el primer punto, tecnica punto a curva
    unosolo = []
    unosolo.append(listaMedidas[0])
    trazaMejorada.append(puntoACurvaArea(listaPlanimetria, segmentos, unosolo, km)[0])
    i = 1
    numeroPuntosTotales = len(listaMedidas)
    while i < len(listaMedidas):
        print("("+str(i)+"/"+str(numeroPuntosTotales)+")")
        #Elegir segmentos candidatos utilizando punto a punto
        #Calcular distancia a todos los puntos
        nodo = listaMedidas[i]
        valorNodo = utm.from_latlon(nodo.lat, nodo.lng)

        listaPlanimetriaEnArea = []
        #Miro los nodos que estén en el area de alrededor (radio de 50 metros)
        '''for nodoPlano in listaPlanimetria:
            if dentroDeArea(nodoPlano, nodo, km) == True:
                listaPlanimetriaEnArea.append(nodoPlano)'''

        #Miramos los segmentos que estén dentro del area
        listaSegmentosArea = []
        for segmento in segmentos:
            if dentroDeArea(segmento.nodoA, nodo, km) == True or dentroDeArea(segmento.nodoB, nodo, km) == True:
                listaSegmentosArea.append(segmento)
                if segmento.nodoA not in listaPlanimetriaEnArea:
                    listaPlanimetriaEnArea.append(segmento.nodoA)
                if segmento.nodoB not in listaPlanimetriaEnArea:
                    listaPlanimetriaEnArea.append(segmento.nodoB)

        dist = []
        for nodoPlano in listaPlanimetriaEnArea:
            valorNodoPlano = utm.from_latlon(nodoPlano.lat, nodoPlano.lng)
            a = numpy.array((valorNodo[0], valorNodo[1]))
            b = numpy.array((valorNodoPlano[0], valorNodoPlano[1]))
            distanciaCalculada = numpy.linalg.norm(a-b)

            #distanciaCalculada = haversine(nodo.lng, nodo.lat, nodoPlano.lng, nodoPlano.lat)
            dist.append(distanciaCalculada)

        #Obtengo el los indices sobre el array inicial de los valores ordenados
        dist_ord = numpy.sort(dist)
        indices = numpy.argsort(dist)

        dist = []

        #numero de candidatos
        num_candidatos = 1
        #numero de nodos comprobados
        n_nodo = 0
        candidates = []

        #Seguimos hasta alcanzar el numero minimo de candidatos
        while num_candidatos < num_min_candidatos and n_nodo < (len(listaPlanimetriaEnArea))+1:
           j=0
           #buscamos segmentos que tienen por extremo el nodo mas cercano
           while j < len(listaSegmentosArea) and num_candidatos < num_min_candidatos+1:
               indexNodoA = index_by_id(listaPlanimetriaEnArea, listaSegmentosArea[j].nodoA)
               indexNodoB = index_by_id(listaPlanimetriaEnArea, listaSegmentosArea[j].nodoB)
               if indexNodoA == indices[n_nodo] or indexNodoB == indices[n_nodo] and len(numpy.where(candidates == j))==0:
                   candidates.append(j)
                   num_candidatos= num_candidatos +1
               j=j+1
           n_nodo = n_nodo+1

        #Calcular la longitud del segmento actual
        valorSegmentoA = utm.from_latlon(nodo.lat, nodo.lng)
        valorSegmentoB = utm.from_latlon(listaMedidas[i-1].lat, listaMedidas[i-1].lng)
        a = numpy.array((valorSegmentoA[0], valorSegmentoA[1]))
        b = numpy.array((valorSegmentoB[0], valorSegmentoB[1]))
        long_actual = numpy.linalg.norm(a-b)
        if long_actual == 0.0:
            print("0")
            trazaMejorada.append(trazaMejorada[i-1])
        else:
            areas = []
            for k in xrange(len(candidates)):
                #Calcular area entre el segmento actual y el segmento candidato

                #Vertices del poligono
                X = []
                valorNodoAnterior = utm.from_latlon(listaMedidas[i-1].lat, listaMedidas[i-1].lng)
                valorNodoActual = valorNodo
                valorNodoA = utm.from_latlon(listaSegmentosArea[candidates[k]].nodoA.lat, listaSegmentosArea[candidates[k]].nodoA.lng)
                valorNodoB = utm.from_latlon(listaSegmentosArea[candidates[k]].nodoB.lat, listaSegmentosArea[candidates[k]].nodoB.lng)
                puntos = numpy.array([[valorNodoAnterior[0], valorNodoAnterior[1]], [valorNodoActual[0], valorNodoActual[1]], [valorNodoA[0], valorNodoA[1]], [valorNodoB[0], valorNodoB[1]]], dtype="float32")
                #ordeno los puntos en el sentido de las agujas del reloj
                puntosOrdenados = order_points(puntos)
                #calculo el area del poligono
                #print(puntosOrdenados)
                #print(puntosOrdenados[:,0])
                #print(puntosOrdenados[:,1])
                poly = PolyArea(puntosOrdenados[:,0], puntosOrdenados[:,1])
                #print(poly)
                areas.append(poly)
                dist.append(poly / long_actual)

            min_index, min_value = min(enumerate(dist), key=operator.itemgetter(1))
            areas = []
            dist = []

            #Corrijo el punto con la tecnica punto a curva sobre el segmento
            segmento_seleccionado = listaSegmentosArea[candidates[min_index]]
            candidates = []

            nodoA = segmento_seleccionado.nodoA
            nodoB = segmento_seleccionado.nodoB
            valorNodoA = utm.from_latlon(nodoA.lat, nodoA.lng)
            valorNodoB = utm.from_latlon(nodoB.lat, nodoB.lng)
            A = numpy.array((valorNodoA[0] ,valorNodoA[1]))
            B = numpy.array((valorNodoB[0] ,valorNodoB[1]))

            #Calculo el vector director del segmento
            D = numpy.subtract(B, A)
            P = numpy.array((valorNodo[0], valorNodo[1]))

            #Calculamos t' de la proyeccion
            normD = numpy.linalg.norm(D)

            #print(D)
            t_calc = 0
            try:
                t_calc = numpy.divide(numpy.dot(numpy.subtract(P, A), numpy.transpose(D)), numpy.dot(normD,normD))
            except RuntimeWarning:
                trazaMejorada.append(trazaMejorada[len(trazaMejorada)-1])
                i = i + 1
                continue

            if t_calc < 0:
                trazaMejorada.append(nodoA)
                #print(nodoA)
            elif t_calc > 1:
                #print(nodoB)
                trazaMejorada.append(nodoB)
            else:
                pprima = A + numpy.dot(t_calc, D)
                pprimaTrans = numpy.transpose(pprima)
                conversion = utm.to_latlon(pprimaTrans[0], pprimaTrans[1], valorNodoA[2], valorNodoA[3])
                #print(conversion)
                trazaMejorada.append(Nodo(conversion[0], conversion[1]))
        i = i+1
    return trazaMejorada

