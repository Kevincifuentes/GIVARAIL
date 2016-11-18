import serial
import math
import atexit
import redis
import requests
import json
from stompy.simple import Client
import time
from test_shared import *
from lib.sim900.inetgsm import SimInetGSM

CONSOLE_LOGGER_LEVEL    = logging.INFO
LOGGER_LEVEL = logging.INFO

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

#Inicializando SIM
port = initializeUartPort(portName="/dev/ttyO1")
(formatter, logger, consoleLogger,) = initializeLogs(LOGGER_LEVEL, CONSOLE_LOGGER_LEVEL)
d = baseOperations(port, logger)
if d is None:
    print("Error al inicializar el modulo SIM.")
    logger.error("Error al inicializar el modulo SIM.")
    exit(0)

(gsm, imei) = d

inet = SimInetGSM(port, logger)

logger.info("attaching GPRS")
if not inet.attachGPRS("telefonica.es", "", "", 1):
    print("Error al abrir internet en el modulo SIM.")
    logger.error("Error al abrir internet en el modulo SIM.")
    exit(0)

logger.info("ip = {0}".format(inet.ip))
print("ip="+ format(inet.ip))

while True:
    gps = ser.readline()
    #print(gps)
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
            gps2 = {'idtren': 'tren1', 'latitud':latitud, 'longitud':longitud}
            #r = requests.post("http://dev.mobility.deustotech.eu:8000/posicion", data=json.dumps(gps2))
            if not inet.httpPOST("dev.mobility.deustotech.eu", 8000,"/posicion",json.dumps(gps2)):
                print("[ERROR]: No se ha podido subir los datos")
            else:
                print("Correcto")

    '''
    else:
        fichero.write(gps)
    '''


