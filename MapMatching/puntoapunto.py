import operator
from math import radians, cos, sin, asin, sqrt
from segmento import Segmento, Nodo
import numpy
import utm

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
            #TODO: Habra que modificarlo, dado que aqui utilizo latitud y longitud
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


#def curvaACurvaa(listaPlanimetria, listaMedidas):

