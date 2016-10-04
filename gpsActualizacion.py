import serial
import math
import atexit
import redis
import json
from stompy.simple import Client
import time

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
        print("Can't calculate from {0} side {1}".format(latlon, side))
        val = None
    return val

ser = serial.Serial()
ser.baudrate = 115200
ser.port = '/dev/ttyACM0'
almacenamientoRedis = redis.StrictRedis(host='localhost', port=6379, db=0)

def toFloat( value):
    val = None
    val = float(value)
    return val

def finalizar():
    print("FIN")

atexit.register(finalizar)

ser.open()

if not ser.isOpen():
    print("Unable to open serial port!")
    raise SystemExit

#Pone el baudrate a 115200 (NECESARIO PARA RECIBIR TODOS LOS MENSAJES)
ser.write("\xB5\x62\x06\x00\x14\x00\x01\x00\x00\x00\xD0\x08\x00\x00\x00\xC2")
ser.write("\x01\x00\x03\x00\x03\x00\x00\x00\x00\x00\xBC\x5E")

#Pone el GPS a la frecuencia de 2hz
ser.write("\xB5\x62\x06\x08\x06\x00\xF4\x01\x01\x00\x01\x00\x0B\x77")
ser.readline()
primera = True

stomp = Client(host='10.45.1.162', port=61613)
stomp.connect()
while True:
    gps = ser.readline()
    '''
    if (gps.startswith('$GNRMC')):
        if(primera == True):
            primera = False
        else:
            fichero.close()
        print("$GNRMC")
        tiempoActual = datetime.now().strftime("%d%m%y_%H%M%S%f")
        nombreFichero = '/media/card/gps_'+ tiempoActual +'.txt'
        fichero = open(nombreFichero, "wb")
        fichero.write(gps)
    if (gps.startswith('$GNZDA')):
        fichero.write(gps)
    if (gps.startswith('$GNTXT')):
        #No hacer nada
        print("Empieza")
    '''
    #Mensaje que nos proporciona la posicion
    if(gps.startswith('$GNGGA')):
        GGA = gps.split(',')
        if(GGA[2]!= '' and GGA[3]!= ''):
            latitud = toDoubleLatLong(GGA[2],GGA[3])
            longitud = toDoubleLatLong(GGA[4],GGA[5])
            altitudMetros = toFloat(GGA[9])
            altitudGrados = toFloat(GGA[11])
            gps2 = {'latitud':latitud, 'longitud':longitud}
            stomp.put(json.dumps(gps2), destination="/queue/jms.topic.test", conf={"type":"posicion"})
    '''
    else:
        fichero.write(gps)
    '''


