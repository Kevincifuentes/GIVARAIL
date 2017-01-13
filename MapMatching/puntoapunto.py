import operator
from math import radians, cos, sin, asin, sqrt
import numpy

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
        distancias = []
        for nodoPlano in listaPlanimetria:
            distanciaCalculada = haversine(nodo.lng, nodo.lat, nodoPlano.lng, nodoPlano.lat)
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
        t_calc = []
        d = []
        for j in xrange(len(segmentos)):
            #TODO: Habra que modificarlo, dado que aqui utilizo latitud y longitud
            A = numpy.array((listaPlanimetria[segmentos[j].indexAx].lng ,listaPlanimetria[segmentos[j].indexAy].lat))
            B = numpy.array((listaPlanimetria[segmentos[j].indexBx].lng ,listaPlanimetria[segmentos[j].indexBy].lat))

