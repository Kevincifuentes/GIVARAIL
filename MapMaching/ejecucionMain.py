from segmento import Segmento, Nodo
from mapmaching import puntoApunto, puntoACurva, curvaACurvaa
import csv
import math
from xml.dom import minidom

def toDoubleLatLong(latlon, side):
    val = None
    try:
        tmp = float(latlon)
        tmp /= 100
        val = math.floor(tmp)
        tmp = (tmp - val) * 100
        val += tmp/60
        tmp -= math.floor(tmp)
        tmp *= 60
        if ((side.upper() == "S") or (side.upper()=="W")):
            val *= -1
    except ValueError:
        print("HILOGPS: Can't calculate from {0} side {1}".format(latlon, side))
        val = None
    return val

def ejecucionPuntoAPunto(listaPlanimetria, listaMedidas):

    listaSolucion = puntoApunto(listaPlanimetria, listaMedidas)

    with open('pointtopoint_240117_175525457130_extended.csv', 'wb') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(['latitude', 'longitude', 'name'])
        for item in listaSolucion:
            spamwriter.writerow([item.lat, item.lng, 'pointtopoint_extended_240117'])

def ejecucionPuntoACurva(listaPlanimetria, listaMedidas):

    segmentos = []

    index = 1
    while index < len(listaPlanimetria):
        if index != len(listaPlanimetria)-1:
            segmentos.append(Segmento(listaPlanimetria[index-1], listaPlanimetria[index]))
        index = index + 1

    listaSolucion = puntoACurva(listaPlanimetria, segmentos, listaMedidas)

    contador = 0
    with open('pointtocurve_240117_175525457130.csv', 'wb') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(['latitude', 'longitude', 'name'])
        for item in listaSolucion:
            spamwriter.writerow([item.lat, item.lng, 'pointtocurve_240117'])
            contador = contador + 1

def ejecucionCurvaACurva(listaPlanimetria, listaMedidas):

    segmentos = []

    index = 1
    while index < len(listaPlanimetria):
        if index != len(listaPlanimetria)-1:
            segmentos.append(Segmento(listaPlanimetria[index-1], listaPlanimetria[index]))
        index = index + 1

    listaSolucion = curvaACurvaa(listaPlanimetria, segmentos, listaMedidas)

    contador = 0
    with open('curvetocurve_240117_175525457130.csv', 'wb') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(['latitude', 'longitude', 'name'])
        for item in listaSolucion:
            spamwriter.writerow([item.lat, item.lng, 'curvetocurve_240117'])
            contador = contador + 1


#INICIO
def main():
    listaMedidas = []

    with open('valoresPrueba_240117_175525457130_formatLatLng.csv', 'rb') as csvfile:
         spamreader = csv.reader(csvfile, delimiter=';', quotechar='|')
         for row in spamreader:
             stringarray = row[0].split(",")
             latitud = float(stringarray[0])
             longitud = float(stringarray[1])
             if latitud != 0 or longitud != 0:
                listaMedidas.append(Nodo(latitud, longitud))

    xmldoc = minidom.parse('240117_Planimetria_extendida.gpx')
    itemlist = xmldoc.getElementsByTagName('trkpt')
    listaPlanimetria = []
    for trkpt in itemlist:
        latPlan = float(trkpt.attributes['lat'].value)
        lngPlan = float(trkpt.attributes['lon'].value)
        listaPlanimetria.append(Nodo(latPlan,lngPlan))


    ejecucionPuntoAPunto(listaPlanimetria, listaMedidas)
    #ejecucionPuntoACurva(listaPlanimetria, listaMedidas)
    #ejecucionCurvaACurva(listaPlanimetria, listaMedidas)

if __name__ == "__main__":
    main()
