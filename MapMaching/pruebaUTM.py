import utm
import datetime

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

print(datetime.datetime.fromtimestamp(1.48575832256e+12/1000.0))
