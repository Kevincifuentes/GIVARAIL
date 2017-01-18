import utm

from segmento import Segmento, Nodo
var = utm.from_latlon(51.2, 7.5)

print(utm.to_latlon(var[0], var[1], var[2], var[3]))


import numpy

a = numpy.array((1, 10))
b = numpy.array((15, 2))

sub = a + b
print(sub)

n = Nodo(1,2)
s = Segmento(n,n)
print(s.nodoA.lat)

print(numpy.transpose(a))
