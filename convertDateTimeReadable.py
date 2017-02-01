import math
import csv
import time
from datetime import datetime

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
with open('valoresPrueba_250117_071426219163_format.csv', 'wb') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    with open('valoresPrueba_250117_071426219163.csv', 'rb') as csvfile:
     spamreader = csv.reader(csvfile, delimiter=';', quotechar='|')
     for row in spamreader:
         stringarray = row[0].split(",")
         latitud = stringarray[0]
         longitud = stringarray[1]
         altitud = stringarray[2]
         aceleracionX = stringarray[3]
         aceleracionY = stringarray[4]
         aceleracionZ = stringarray[5]
         giroscopioX = stringarray[6]
         giroscopioY = stringarray[7]
         giroscopioZ = stringarray[8]
         magnetometroX = stringarray[9]
         magnetometroY = stringarray[10]
         magnetometroZ = stringarray[11]
         yaw = stringarray[12]
         pitch = stringarray[13]
         roll = stringarray[14]
         barometro = stringarray[15]
         hdop = stringarray[16]
         vdop = stringarray[17]
         pdop = stringarray[18]
         timeStamp = stringarray[19]
         stringTime = '0'
         if timeStamp != 0 and timeStamp != '0' :
             print timeStamp
             datetime_object = datetime.strptime(timeStamp, '%d-%m-%y %H:%M:%S.%f')
             stringTime = str(time.mktime(datetime_object.timetuple())*1e3 + datetime_object.microsecond/1e3)
         resultado =latitud+","+longitud+","+altitud+","+aceleracionX+","+aceleracionY+","+aceleracionZ+","+giroscopioX+","+giroscopioY+","+giroscopioZ+","+magnetometroX+","+magnetometroY+","+magnetometroZ+","+yaw+","+pitch+","+roll+","+barometro+","+hdop+","+vdop+","+pdop+","+stringTime+";\n"
         spamwriter.writerow([latitud, longitud, altitud, aceleracionX, aceleracionY, aceleracionZ, giroscopioX, giroscopioY, giroscopioZ, magnetometroX, magnetometroY, magnetometroZ, yaw, pitch, roll, barometro, hdop, vdop, pdop, stringTime])





