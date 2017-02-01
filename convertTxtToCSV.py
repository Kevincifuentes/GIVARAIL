import math
import csv

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
primeraVEZ = True
contador = 1
with open('excellFormateado.csv', 'wb') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    with open('25.csv', 'rb') as csvfile:
     spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
     for row in spamreader:
         stringarray = row[0].split(",")
         latitud = stringarray[0]
         longitud = stringarray[1]
         if primeraVEZ:
             primeraVEZ = False
             spamwriter.writerow(['latitude', 'longitude', 'name'])
         else:
             if latitud != '0' and longitud != '0':
                 spamwriter.writerow([toDoubleLatLong(latitud, "N"), toDoubleLatLong(longitud, "W"), 'prueba_250117'])
                 contador = contador + 1





