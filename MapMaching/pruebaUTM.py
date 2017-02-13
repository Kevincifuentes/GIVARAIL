import utm
import datetime
import math

def arePointsNear(checkPoint, centerPoint, km):
    ky = 40000 / 360;
    kx = math.cos(math.pi * centerPoint[0] / 180.0) * ky;
    dx = math.fabs(centerPoint[1] - checkPoint[1]) * kx;
    dy = math.fabs(centerPoint[0] - checkPoint[0]) * ky;
    return math.sqrt(dx * dx + dy * dy) <= km;


vasteras = [43.270126, -2.939200 ];
stockholm = [43.270142, -2.939343 ];

n = arePointsNear(vasteras, stockholm, 0.05);

print(n)

from segmento import Segmento, Nodo
var = utm.from_latlon(42.973232, -3.543137)
print(var)
print(utm.to_latlon(var[0], var[1], var[2], var[3]))

print(utm.to_latlon(462779.86746679,  4761005.93085541, 30, var[3]))

import numpy

a = numpy.array((1, 10))
b = numpy.array((15, 2))

sub = a + b
print(sub)

n = Nodo(1,2)
s = Segmento(n,n)
print(s.nodoA.lat)

print(numpy.transpose(a))

print(datetime.datetime.fromtimestamp(1.48671117865e+12/1000.0))
