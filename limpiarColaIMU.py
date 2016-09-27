import redis


almacenamientoRedis = redis.StrictRedis(host='localhost', port=6379, db=0)
valoresIMU = almacenamientoRedis.rpop('cola_imu')
while(valoresIMU!=None):
    valoresIMU = almacenamientoRedis.rpop('cola_imu')
print("FIN Limpieza IMU")
