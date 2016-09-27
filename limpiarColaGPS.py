
import redis


almacenamientoRedis = redis.StrictRedis(host='localhost', port=6379, db=0)
posicion = almacenamientoRedis.rpop('cola_gps')
while(posicion!=None):
    posicion = almacenamientoRedis.rpop('cola_gps')
print("FIN Limpieza GPS")
