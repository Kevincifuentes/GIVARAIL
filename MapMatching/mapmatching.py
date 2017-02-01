import operator
from math import radians, cos, sin, asin, sqrt
from segmento import Segmento, Nodo
import numpy
import utm
from scipy.spatial import distance as dist
import numpy
import cv2


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
    for nodo in listaMedidas:
        #Para cada uno de los nodos medidos calculo la distancia
        #a cada punto del plano
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
        min_index, min_value = min(enumerate(distancias), key=operator.itemgetter(1))
        trazaMejorada.append(listaPlanimetria[min_index])

    return trazaMejorada


def puntoACurva(listaPlanimetria, segmentos, listaMedidas):
    """
    Funcion que calcula la traza mejorada utilizando la tecnica punto a curva
    """
    trazaMejorada = []
    for i in xrange(len(listaMedidas)):
        #Para cada punto del camino se comprueba la distancia con cada segmento
        #y se coge el segmento con menor distancia
        nodo = listaMedidas[i]
        valorNodoReal = utm.from_latlon(nodo.lat, nodo.lng)
        nodoReal = numpy.array((valorNodoReal[0] ,valorNodoReal[1]))
        t_calc = []
        d = []
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
            t_calc[j] = numpy.divide(numpy.multiply(numpy.subtract(nodoReal, A), numpy.transpose(D)), numpy.multiply(normD,normD))

            if t_calc[j] < 0:
                d[j] = numpy.linalg.norm(numpy.subtract(nodoReal, A))
            elif t_calc[j] > 1:
                d[j] = numpy.linalg.norm(numpy.subtract(nodoReal, B))
            else:
                pprima = A + numpy.multiply(t_calc[j], D)
                d[j] = numpy.linalg.norm(numpy.subtract(pprima, nodoReal))

            #Obtengo el mínimo de todos ellos
            j, min_value = min(enumerate(d), key=operator.itemgetter(1))
            nodoA = segmentos[j].nodoA
            nodoB = segmentos[j].nodoB
            valorNodoA = utm.from_latlon(nodoA.lat, nodoA.lng)
            valorNodoB = utm.from_latlon(nodoB.lat, nodoB.lng)
            A = numpy.array((valorNodoA[0] ,valorNodoA[1]))
            D = numpy.subtract(B, A)

            #Tengo que convertirlos de nuevo a lat/lng
            #easting, northing, zone_number, zone_letter
            if t_calc[j] < 0:
                a = utm.to_latlon(valorNodoA[0], valorNodoA[1], valorNodoA[2], valorNodoA[3])
                trazaMejorada[j] = Nodo(a[0], a[1])
            elif t_calc[j] > 1:
                b = utm.to_latlon(valorNodoB[0], valorNodoB[1], valorNodoB[2], valorNodoB[3])
                trazaMejorada[j] = Nodo(b[0], b[1])
            else:
                pprima = A + numpy.multiply(t_calc[j], D)
                d[j] = numpy.transpose(pprima)
    return trazaMejorada


def curvaACurvaa(listaPlanimetria, segmentos, listaMedidas):
    """
    Funcion que calcula la traza mejorada utilizando la tecnica curva a curva
    """
    num_min_candidatos = 2
    trazaMejorada = []
    #Para el primer punto, tecnica punto a curva
    trazaMejorada[0] = puntoACurva(listaPlanimetria, segmentos, listaMedidas[0])
    i = 1
    while i < xrange(len(listaMedidas)):
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
           while j < len(segmentos)+1 and num_candidatos < num_min_candidatos+1:
               indexNodoA = listaPlanimetria.index(segmentos[j].nodoA)
               indexNodoB = listaPlanimetria.index(segmentos[j].nodoB)
               if indexNodoA == indices[n_nodo] or indexNodoB == indices[n_nodo] and len(numpy.where(candidates == j))==0:
                   candidates[num_candidatos] = j
                   num_candidatos= num_candidatos +1
               j=j+1
           n_nodo = n_nodo+1

        #Calcular la longitud del segmento actual
        valorSegmentoA = utm.from_latlon(nodo.lat, nodo.lng)
        valorSegmentoB = utm.from_latlon(listaMedidas[i-1].lat, listaMedidas[i-1].lng)
        a = numpy.array((valorSegmentoA[0], valorSegmentoA[1]))
        b = numpy.array((valorSegmentoB[0], valorSegmentoB[1]))
        long_actual = numpy.linalg.norm(a-b)

        areas = []
        for k in len(candidates):
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
            areas[k] = PolyArea(puntosOrdenados[:,0], puntosOrdenados[:,1])
            dist[k] = areas[k] / long_actual

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
        P = numpy.array(valorNodo[0], valorNodo[1])

        #Calculamos t' de la proyeccion
        normD = numpy.linalg.norm(D)
        t_calc = numpy.divide(numpy.multiply(numpy.subtract(P, A), numpy.transpose(D)), numpy.multiply(normD,normD))

        if t_calc < 0:
            trazaMejorada[i] = nodoA
        elif t_calc > 1:
            trazaMejorada[i] = nodoB
        else:
            pprima = A + numpy.multiply(t_calc, D)
            trazaMejorada[i] = numpy.transpose(pprima)
        i = i+1


