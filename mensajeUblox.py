import sys
import binascii

cs0=0
cs1=0

sys.stdout.write("\xb5\x62")

for d in sys.argv[1:]:
  c = binascii.unhexlify(d)
  sys.stdout.write(c)
  cs0 += ord(c)
  cs0 &= 255
  cs1 += cs0
  cs1 &= 255
  print(cs0)

sys.stdout.write(chr(cs0)+chr(cs1))
