import serial
import serial

serial = serial.Serial("/dev/ttyO1", baudrate=115200, timeout=3.0)
serial.open()
print("Starting...");
serial.available

