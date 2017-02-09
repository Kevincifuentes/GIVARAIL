#!/usr/bin/env python

from datetime import datetime
import serial
import re
import sys
import json
import redis
import logging
import time
import struct
import atexit

from mtdef import MID, OutputMode, OutputSettings, MTException, Baudrates, \
    XDIGroup, getMIDName, DeviceState, DeprecatedMID, MTErrorMessage, \
    MTTimeoutException

class ExitHooks(object):
    def __init__(self):
        self.exit_code = None
        self.exception = None

    def hook(self):
        self._orig_exit = sys.exit
        sys.exit = self.exit
        sys.excepthook = self.exc_handler

    def exit(self, code=0):
        self.exit_code = code
        self._orig_exit(code)

    def exc_handler(self, exc_type, exc, *args):
        self.exception = exc

hooks = ExitHooks()
hooks.hook()

global almacenamientoRedis
almacenamientoRedis = redis.StrictRedis(host='localhost', port=6379, db=0)

def finalizar():
    try:
        envioBajoNivel(ser, MID.Reset)
        leerBajoNivel(ser)
    except Exception:
        print()
    ser.close()
    if hooks.exit_code is not None:
        print("ERROR: Desechufa la IMU y Reinicia el proceso")
        logging.error("HiloIMU muerto por Sys.exit(%d)" % hooks.exit_code)
    elif hooks.exception is not None:
        print("ERROR: Desechufa la IMU y Reinicia el proceso")
        logging.error("HiloIMU muerto por Excepcion: %s" % hooks.exception)
        error = {'error': 'error'}
        try:
            almacenamientoRedis.lpush('cola_imu', json.dumps(error))
        except KeyboardInterrupt:
            print("Interupcion IMU al enviar error")
    else:
        logging.error("Muerte natural")
    print("Fin del HiloIMU")
    logging.info('HILOIMU terminado.')

def leerValores(ser, mode=OutputMode.Calib, settings=OutputSettings.Coordinates_NED):
        # getting data
        # data = self.read_data_msg()
        mid, data = leerBajoNivel(ser)
        if mid == MID.MTData:
            return parse_MTData(data, mode, settings)
        elif mid == MID.MTData2:
            return parse_MTData2(data)
        else:
            #raise MTException("unknown data message: mid=0x%02X (%s)." %  (mid, getMIDName(mid)))
            #print("error")
            envioBajoNivel(ser, MID.GoToMeasurement)
            leerBajoNivel(ser)

def envioBajoNivel(ser, mid, data=b''):
        """Low-level message sending function."""
        length = len(data)
        if length > 254:
            lendat = b'\xFF' + struct.pack('!H', length)
        else:
            lendat = struct.pack('!B', length)
        packet = b'\xFA\xFF' + struct.pack('!B', mid) + lendat + data
        packet += struct.pack('!B', 0xFF & (-(sum(map(ord, packet[1:])))))
        msg = packet
        start = time.time()
        while ((time.time()-start) < ser.timeout) and ser.read():
            pass
        ser.write(msg)
        #print("HILOIMU: Envio realizado")
        #if self.verbose:
        #    print "MT: Write message id 0x%02X (%s) with %d data bytes: [%s]" %\
        #        (mid, getMIDName(mid), length,
        #         ' '.join("%02X" % ord(v) for v in data))

def leerBajoNivel(ser):
        """Low-level message receiving function."""
        start = time.time()
        while (time.time()-start) < ser.timeout:
            # first part of preamble
            if ord(esperando(ser, 1)) != 0xFA:
                continue

            # second part of preamble
            if ord(esperando(ser, 1)) != 0xFF:  # we assume no timeout anymore
                continue
            # read message id and length of message
            mid, length = struct.unpack('!BB', esperando(ser, 2))
            if length == 255:    # extended length
                length, = struct.unpack('!H', esperando(ser, 2))
            # read contents and checksum
            buf = esperando(ser, length+1)
            checksum = buf[-1]
            data = struct.unpack('!%dB' % length, buf[:-1])
            #print("HILOIMU: LeerBajoNivel: id 0x%02X (%s)", mid, getMIDName(mid))
            # check message integrity
            #if 0xFF & sum(data, 0xFF+mid+length+checksum):
            #    if self.verbose:
            #        sys.stderr.write("invalid checksum; discarding data and "
            #                         "waiting for next message.\n")
            #    continue
            #if self.verbose:
            #    print "MT: Got message id 0x%02X (%s) with %d data bytes: [%s]"\
            #        % (mid, getMIDName(mid), length,
            #           ' '.join("%02X" % v for v in data))
            #if mid == MID.Error:
            #    raise MTErrorMessage(data[0])
            return (mid, buf[:-1])

def esperando(ser, size=1):
        """Get a given amount of data."""
        buf = bytearray()
        for _ in range(100):
            buf.extend(ser.read(size-len(buf)))
            if len(buf) == size:
                return buf
        logging.error("HILOIMU: waiting for %d bytes, got %d so far: [%s]" % \
                    (size, len(buf), ' '.join('%02X' % v for v in buf)))
        raise MTTimeoutException("waiting for message")

def escribirACK(ser, mid, data=b'', n_retries=500):
        """Send a message and read confirmation."""
        envioBajoNivel(ser, mid, data)
        for _ in range(n_retries):
            mid_ack, data_ack = leerBajoNivel(ser)
            if mid_ack == (mid+1):
                break
        else:
            raise MTException("Ack (0x%02X) expected, MID 0x%02X received "
                              "instead (after %d retries)." % (mid+1, mid_ack,
                                                               n_retries))
        return data_ack

def obtenerConfiguracion(ser):
        """Ask for the current configuration of the MT device."""
        config = escribirACK(ser, MID.ReqConfiguration)
        try:
            masterID, period, skipfactor, _, _, _, date, time, num, deviceID,\
                length, mode, settings =\
                struct.unpack('!IHHHHI8s8s32x32xHIHHI8x', config)
        except struct.error:
            raise MTException("could not parse configuration.")
        if length <= 254:
            header = b'\xFA\xFF\x32' + struct.pack('!B', length)
        else:
            header = b'\xFA\xFF\x32\xFF' + struct.pack('!H', length)
        conf = {'output-mode': mode,
                'output-settings': settings,
                'length': length,
                'period': period,
                'skipfactor': skipfactor,
                'Master device ID': masterID,
                'date': date,
                'time': time,
                'number of devices': num,
                'device ID': deviceID}
        return conf

def determinarPeriodo(ser, period):
    """Set the sampling period."""
    data = struct.pack('!H', period)
    escribirACK(ser, MID.SetPeriod, data)

def determinarSkipFactor(ser, output):
    data = struct.pack('!H', output)
    escribirACK(ser, DeprecatedMID.SetOutputSkipFactor, data)

def determinarModoOutput(ser, mode):
    """Select which information to output."""
    data = struct.pack('!H', mode)
    escribirACK(ser, MID.SetOutputMode, data)

def determinarConfiguracionOutput(ser, settings):
        """Select how to output the information."""
        data = struct.pack('!I', settings)
        escribirACK(ser, MID.SetOutputSettings, data)

def determinarTiempoUTC(ser, ns, year, month, day, hour, minute, second, flag):
        """Set UTC time on the device."""
        data = struct.pack('!IHBBBBBB', ns, year, month, day, hour, minute,
                           second, flag)  # no clue what setting flag can mean
        escribirACK(ser, MID.SetUTCTime, data)

def parse_MTData2(data):
    # Functions to parse each type of packet
    def parse_temperature(data_id, content, ffmt):
        o = {}
        if (data_id & 0x00F0) == 0x10:  # Temperature
            o['Temp'], = struct.unpack('!'+ffmt, content)
        else:
            raise MTException("unknown packet: 0x%04X." % data_id)
        return o

    def parse_timestamp(data_id, content, ffmt):
        o = {}
        if (data_id & 0x00F0) == 0x10:  # UTC Time
            o['ns'], o['Year'], o['Month'], o['Day'], o['Hour'],\
                o['Minute'], o['Second'], o['Flags'] =\
                struct.unpack('!LHBBBBBB', content)
        elif (data_id & 0x00F0) == 0x20:  # Packet Counter
            o['PacketCounter'], = struct.unpack('!H', content)
        elif (data_id & 0x00F0) == 0x30:  # Integer Time of Week
            o['TimeOfWeek'], = struct.unpack('!L', content)
        elif (data_id & 0x00F0) == 0x40:  # GPS Age  # deprecated
            o['gpsAge'], = struct.unpack('!B', content)
        elif (data_id & 0x00F0) == 0x50:  # Pressure Age  # deprecated
            o['pressureAge'], = struct.unpack('!B', content)
        elif (data_id & 0x00F0) == 0x60:  # Sample Time Fine
            o['SampleTimeFine'], = struct.unpack('!L', content)
        elif (data_id & 0x00F0) == 0x70:  # Sample Time Coarse
            o['SampleTimeCoarse'], = struct.unpack('!L', content)
        elif (data_id & 0x00F0) == 0x80:  # Frame Range
            o['startFrame'], o['endFrame'] = struct.unpack('!HH', content)
        else:
            raise MTException("unknown packet: 0x%04X." % data_id)
        return o

    def parse_orientation_data(data_id, content, ffmt):
        o = {}
        if (data_id & 0x000C) == 0x00:  # ENU
            o['frame'] = 'ENU'
        elif (data_id & 0x000C) == 0x04:  # NED
            o['frame'] = 'NED'
        elif (data_id & 0x000C) == 0x08:  # NWU
            o['frame'] = 'NWU'
        if (data_id & 0x00F0) == 0x10:  # Quaternion
            o['Q0'], o['Q1'], o['Q2'], o['Q3'] = struct.unpack('!'+4*ffmt,
                                                               content)
        elif (data_id & 0x00F0) == 0x20:  # Rotation Matrix
            o['a'], o['b'], o['c'], o['d'], o['e'], o['f'], o['g'], o['h'],\
                o['i'] = struct.unpack('!'+9*ffmt, content)
        elif (data_id & 0x00F0) == 0x30:  # Euler Angles
            o['Roll'], o['Pitch'], o['Yaw'] = struct.unpack('!'+3*ffmt,
                                                            content)
        else:
            raise MTException("unknown packet: 0x%04X." % data_id)
        return o

    def parse_pressure(data_id, content, ffmt):
        o = {}
        if (data_id & 0x00F0) == 0x10:  # Baro pressure
            o['Pressure'], = struct.unpack('!L', content)
        else:
            raise MTException("unknown packet: 0x%04X." % data_id)
        return o

    def parse_acceleration(data_id, content, ffmt):
        o = {}
        if (data_id & 0x000C) == 0x00:  # ENU
            o['frame'] = 'ENU'
        elif (data_id & 0x000C) == 0x04:  # NED
            o['frame'] = 'NED'
        elif (data_id & 0x000C) == 0x08:  # NWU
            o['frame'] = 'NWU'
        if (data_id & 0x00F0) == 0x10:  # Delta V
            o['Delta v.x'], o['Delta v.y'], o['Delta v.z'] = \
                struct.unpack('!'+3*ffmt, content)
        elif (data_id & 0x00F0) == 0x20:  # Acceleration
            o['accX'], o['accY'], o['accZ'] = \
                struct.unpack('!'+3*ffmt, content)
        elif (data_id & 0x00F0) == 0x30:  # Free Acceleration
            o['freeAccX'], o['freeAccY'], o['freeAccZ'] = \
                struct.unpack('!'+3*ffmt, content)
        elif (data_id & 0x00F0) == 0x40:  # AccelerationHR
            o['accX'], o['accY'], o['accZ'] = \
                struct.unpack('!'+3*ffmt, content)
        else:
            raise MTException("unknown packet: 0x%04X." % data_id)
        return o

    def parse_position(data_id, content, ffmt):
        o = {}
        if (data_id & 0x000C) == 0x00:  # ENU
            o['frame'] = 'ENU'
        elif (data_id & 0x000C) == 0x04:  # NED
            o['frame'] = 'NED'
        elif (data_id & 0x000C) == 0x08:  # NWU
            o['frame'] = 'NWU'
        if (data_id & 0x00F0) == 0x10:  # Altitude MSL  # deprecated
            o['altMsl'], = struct.unpack('!'+ffmt, content)
        elif (data_id & 0x00F0) == 0x20:  # Altitude Ellipsoid
            o['altEllipsoid'], = struct.unpack('!'+ffmt, content)
        elif (data_id & 0x00F0) == 0x30:  # Position ECEF
            o['ecefX'], o['ecefY'], o['ecefZ'] = \
                struct.unpack('!'+3*ffmt, content)
        elif (data_id & 0x00F0) == 0x40:  # LatLon
            o['lat'], o['lon'] = struct.unpack('!'+2*ffmt, content)
        else:
            raise MTException("unknown packet: 0x%04X." % data_id)
        return o

    def parse_GNSS(data_id, content, ffmt):
        o = {}
        if (data_id & 0x00F0) == 0x10:  # GNSS PVT data
            o['itow'], o['year'], o['month'], o['day'], o['hour'],\
                o['min'], o['sec'], o['valid'], o['tAcc'], o['nano'],\
                o['fixtype'], o['flags'], o['numSV'], o['lon'], o['lat'],\
                o['height'], o['hMSL'], o['hAcc'], o['vAcc'], o['velN'],\
                o['velE'], o['velD'], o['gSpeed'], o['headMot'], o['sAcc'],\
                o['headAcc'], o['headVeh'], o['gdop'], o['pdop'],\
                o['tdop'], o['vdop'], o['hdop'], o['ndop'], o['edop'] = \
                struct.unpack('!IHBBBBBBIiBBBBiiiiIIiiiiiIIiHHHHHHH',
                              content)
            # scaling correction
            o['lon'] *= 1e-7
            o['lat'] *= 1e-7
            o['headMot'] *= 1e-5
            o['headVeh'] *= 1e-5
            o['gdop'] *= 0.01
            o['pdop'] *= 0.01
            o['tdop'] *= 0.01
            o['vdop'] *= 0.01
            o['hdop'] *= 0.01
            o['bdop'] *= 0.01
            o['edop'] *= 0.01
        elif (data_id & 0x00F0) == 0x20:  # GNSS satellites info
            o['iTOW'], o['numSvs'] = struct.unpack('!LBxxx', content[:8])
            svs = []
            ch = {}
            for i in range(o['numSvs']):
                ch['gnssId'], ch['svId'], ch['cno'], ch['flags'] = \
                    struct.unpack('!BBBB', content[8+4*i:12+4*i])
                svs.append(ch)
            o['svs'] = svs
        else:
            raise MTException("unknown packet: 0x%04X." % data_id)
        return o

    def parse_angular_velocity(data_id, content, ffmt):
        o = {}
        if (data_id & 0x000C) == 0x00:  # ENU
            o['frame'] = 'ENU'
        elif (data_id & 0x000C) == 0x04:  # NED
            o['frame'] = 'NED'
        elif (data_id & 0x000C) == 0x08:  # NWU
            o['frame'] = 'NWU'
        if (data_id & 0x00F0) == 0x20:  # Rate of Turn
            o['gyrX'], o['gyrY'], o['gyrZ'] = \
                struct.unpack('!'+3*ffmt, content)
        elif (data_id & 0x00F0) == 0x30:  # Delta Q
            o['Delta q0'], o['Delta q1'], o['Delta q2'], o['Delta q3'] = \
                struct.unpack('!'+4*ffmt, content)
        elif (data_id & 0x00F0) == 0x40:  # RateOfTurnHR
            o['gyrX'], o['gyrY'], o['gyrZ'] = \
                struct.unpack('!'+3*ffmt, content)
        else:
            raise MTException("unknown packet: 0x%04X." % data_id)
        return o

    def parse_GPS(data_id, content, ffmt):
        o = {}
        if (data_id & 0x00F0) == 0x30:  # DOP
            o['iTOW'], g, p, t, v, h, n, e = \
                struct.unpack('!LHHHHHHH', content)
            o['gDOP'], o['pDOP'], o['tDOP'], o['vDOP'], o['hDOP'], \
                o['nDOP'], o['eDOP'] = 0.01*g, 0.01*p, 0.01*t, \
                0.01*v, 0.01*h, 0.01*n, 0.01*e
        elif (data_id & 0x00F0) == 0x40:  # SOL
            o['iTOW'], o['fTOW'], o['Week'], o['gpsFix'], o['Flags'], \
                o['ecefX'], o['ecefY'], o['ecefZ'], o['pAcc'], \
                o['ecefVX'], o['ecefVY'], o['ecefVZ'], o['sAcc'], \
                o['pDOP'], o['numSV'] = \
                struct.unpack('!LlhBBlllLlllLHxBx', content)
            # scaling correction
            o['pDOP'] *= 0.01
        elif (data_id & 0x00F0) == 0x80:  # Time UTC
            o['iTOW'], o['tAcc'], o['nano'], o['year'], o['month'], \
                o['day'], o['hour'], o['min'], o['sec'], o['valid'] = \
                struct.unpack('!LLlHBBBBBB', content)
        elif (data_id & 0x00F0) == 0xA0:  # SV Info
            o['iTOW'], o['numCh'] = struct.unpack('!LBxxx', content[:8])
            channels = []
            ch = {}
            for i in range(o['numCh']):
                ch['chn'], ch['svid'], ch['flags'], ch['quality'], \
                    ch['cno'], ch['elev'], ch['azim'], ch['prRes'] = \
                    struct.unpack('!BBBBBbhl', content[8+12*i:20+12*i])
                channels.append(ch)
            o['channels'] = channels
        else:
            raise MTException("unknown packet: 0x%04X." % data_id)
        return o

    def parse_SCR(data_id, content, ffmt):
        o = {}
        if (data_id & 0x00F0) == 0x10:  # ACC+GYR+MAG+Temperature
            o['accX'], o['accY'], o['accZ'], o['gyrX'], o['gyrY'], \
                o['gyrZ'], o['magX'], o['magY'], o['magZ'], o['Temp'] = \
                struct.unpack("!9Hh", content)
        elif (data_id & 0x00F0) == 0x20:  # Gyro Temperature
            o['tempGyrX'], o['tempGyrY'], o['tempGyrZ'] = \
                struct.unpack("!hhh", content)
        else:
            raise MTException("unknown packet: 0x%04X." % data_id)
        return o

    def parse_analog_in(data_id, content, ffmt):  # deprecated
        o = {}
        if (data_id & 0x00F0) == 0x10:  # Analog In 1
            o['analogIn1'], = struct.unpack("!H", content)
        elif (data_id & 0x00F0) == 0x20:  # Analog In 2
            o['analogIn2'], = struct.unpack("!H", content)
        else:
            raise MTException("unknown packet: 0x%04X." % data_id)
        return o

    def parse_magnetic(data_id, content, ffmt):
        o = {}
        if (data_id & 0x000C) == 0x00:  # ENU
            o['frame'] = 'ENU'
        elif (data_id & 0x000C) == 0x04:  # NED
            o['frame'] = 'NED'
        elif (data_id & 0x000C) == 0x08:  # NWU
            o['frame'] = 'NWU'
        if (data_id & 0x00F0) == 0x20:  # Magnetic Field
            o['magX'], o['magY'], o['magZ'] = \
                struct.unpack("!3"+ffmt, content)
        else:
            raise MTException("unknown packet: 0x%04X." % data_id)
        return o

    def parse_velocity(data_id, content, ffmt):
        o = {}
        if (data_id & 0x000C) == 0x00:  # ENU
            o['frame'] = 'ENU'
        elif (data_id & 0x000C) == 0x04:  # NED
            o['frame'] = 'NED'
        elif (data_id & 0x000C) == 0x08:  # NWU
            o['frame'] = 'NWU'
        if (data_id & 0x00F0) == 0x10:  # Velocity XYZ
            o['velX'], o['velY'], o['velZ'] = \
                struct.unpack("!3"+ffmt, content)
        else:
            raise MTException("unknown packet: 0x%04X." % data_id)
        return o

    def parse_status(data_id, content, ffmt):
        o = {}
        if (data_id & 0x00F0) == 0x10:  # Status Byte
            o['StatusByte'], = struct.unpack("!B", content)
        elif (data_id & 0x00F0) == 0x20:  # Status Word
            o['StatusWord'], = struct.unpack("!L", content)
        elif (data_id & 0x00F0) == 0x40:  # RSSI  # deprecated
            o['RSSI'], = struct.unpack("!b", content)
        else:
            raise MTException("unknown packet: 0x%04X." % data_id)
        return o

    # data object
    output = {}
    while data:
        try:
            data_id, size = struct.unpack('!HB', data[:3])
            if (data_id & 0x0003) == 0x3:
                float_format = 'd'
            elif (data_id & 0x0003) == 0x0:
                float_format = 'f'
            else:
                raise MTException("fixed point precision not supported.")
            content = data[3:3+size]
            data = data[3+size:]
            group = data_id & 0xF800
            ffmt = float_format
            if group == XDIGroup.Temperature:
                output.setdefault('Temperature', {}).update(
                    parse_temperature(data_id, content, ffmt))
            elif group == XDIGroup.Timestamp:
                output.setdefault('Timestamp', {}).update(
                    parse_timestamp(data_id, content, ffmt))
            elif group == XDIGroup.OrientationData:
                output.setdefault('Orientation Data', {}).update(
                    parse_orientation_data(data_id, content, ffmt))
            elif group == XDIGroup.Pressure:
                output.setdefault('Pressure', {}).update(
                    parse_pressure(data_id, content, ffmt))
            elif group == XDIGroup.Acceleration:
                output.setdefault('Acceleration', {}).update(
                    parse_acceleration(data_id, content, ffmt))
            elif group == XDIGroup.Position:
                output.setdefault('Position', {}).update(
                    parse_position(data_id, content, ffmt))
            elif group == XDIGroup.GNSS:
                output.setdefault('GNSS', {}).update(
                    parse_GNSS(data_id, content, ffmt))
            elif group == XDIGroup.AngularVelocity:
                output.setdefault('Angular Velocity', {}).update(
                    parse_angular_velocity(data_id, content, ffmt))
            elif group == XDIGroup.GPS:
                output.setdefault('GPS', {}).update(
                    parse_GPS(data_id, content, ffmt))
            elif group == XDIGroup.SensorComponentReadout:
                output.setdefault('SCR', {}).update(
                    parse_SCR(data_id, content, ffmt))
            elif group == XDIGroup.AnalogIn:  # deprecated
                output.setdefault('Analog In', {}).update(
                    parse_analog_in(data_id, content, ffmt))
            elif group == XDIGroup.Magnetic:
                output.setdefault('Magnetic', {}).update(
                    parse_magnetic(data_id, content, ffmt))
            elif group == XDIGroup.Velocity:
                output.setdefault('Velocity', {}).update(
                    parse_velocity(data_id, content, ffmt))
            elif group == XDIGroup.Status:
                output.setdefault('Status', {}).update(
                    parse_status(data_id, content, ffmt))
            else:
                raise MTException("unknown XDI group: 0x%04X." % group)
        except struct.error:
            raise MTException("couldn't parse MTData2 message.")
    return output
def parse_MTData(data, mode=OutputMode.Calib, settings=None):
    """Read and parse a legacy measurement packet."""
    # getting mode
    # data object
    output = {}
    try:
        # raw IMU first
        if mode & OutputMode.RAW:
            o = {}
            o['accX'], o['accY'], o['accZ'], o['gyrX'], o['gyrY'], \
                o['gyrZ'], o['magX'], o['magY'], o['magZ'], o['temp'] =\
                struct.unpack('!10H', data[:20])
            data = data[20:]
            output['RAW'] = o
        # raw GPS second
        if mode & OutputMode.RAWGPS:
            o = {}
            o['Press'], o['bPrs'], o['ITOW'], o['LAT'], o['LON'], o['ALT'],\
                o['VEL_N'], o['VEL_E'], o['VEL_D'], o['Hacc'], o['Vacc'],\
                o['Sacc'], o['bGPS'] = struct.unpack('!HBI6i3IB', data[:44])
            data = data[44:]
            output['RAWGPS'] = o
        # temperature
        if mode & OutputMode.Temp:
            temp, = struct.unpack('!f', data[:4])
            data = data[4:]
            output['Temp'] = temp
        # calibrated data
        if mode & OutputMode.Calib:
            o = {}
            if (settings & OutputSettings.Coordinates_NED):
                o['frame'] = 'NED'
            else:
                o['frame'] = 'ENU'
            if not (settings & OutputSettings.CalibMode_GyrMag):
                o['accX'], o['accY'], o['accZ'] = struct.unpack('!3f',
                                                                data[:12])
                data = data[12:]
            if not (settings & OutputSettings.CalibMode_AccMag):
                o['gyrX'], o['gyrY'], o['gyrZ'] = struct.unpack('!3f',
                                                                data[:12])
                data = data[12:]
            if not (settings & OutputSettings.CalibMode_AccGyr):
                o['magX'], o['magY'], o['magZ'] = struct.unpack('!3f',
                                                                data[:12])
                data = data[12:]
            output['Calib'] = o
        # orientation
        if mode & OutputMode.Orient:
            o = {}
            if (settings & OutputSettings.Coordinates_NED):
                o['frame'] = 'NED'
            else:
                o['frame'] = 'ENU'
            if settings & OutputSettings.OrientMode_Euler:
                o['roll'], o['pitch'], o['yaw'] = struct.unpack('!3f',
                                                                data[:12])
                data = data[12:]
            elif settings & OutputSettings.OrientMode_Matrix:
                a, b, c, d, e, f, g, h, i = struct.unpack('!9f',
                                                          data[:36])
                data = data[36:]
                o['matrix'] = ((a, b, c), (d, e, f), (g, h, i))
            else:  # OutputSettings.OrientMode_Quaternion:
                q0, q1, q2, q3 = struct.unpack('!4f', data[:16])
                data = data[16:]
                o['quaternion'] = (q0, q1, q2, q3)
            output['Orient'] = o
        # auxiliary
        if mode & OutputMode.Auxiliary:
            o = {}
            if not (settings & OutputSettings.AuxiliaryMode_NoAIN1):
                o['Ain_1'], = struct.unpack('!H', data[:2])
                data = data[2:]
            if not (settings & OutputSettings.AuxiliaryMode_NoAIN2):
                o['Ain_2'], = struct.unpack('!H', data[:2])
                data = data[2:]
            output['Auxiliary'] = o
        # position
        if mode & OutputMode.Position:
            o = {}
            o['Lat'], o['Lon'], o['Alt'] = struct.unpack('!3f', data[:12])
            data = data[12:]
            output['Pos'] = o
        # velocity
        if mode & OutputMode.Velocity:
            o = {}
            if (settings & OutputSettings.Coordinates_NED):
                o['frame'] = 'NED'
            else:
                o['frame'] = 'ENU'
            o['Vel_X'], o['Vel_Y'], o['Vel_Z'] = struct.unpack('!3f',
                                                               data[:12])
            data = data[12:]
            output['Vel'] = o
        # status
        if mode & OutputMode.Status:
            status, = struct.unpack('!B', data[:1])
            data = data[1:]
            output['Stat'] = status
        # sample counter
        if settings & OutputSettings.Timestamp_SampleCnt:
            TS, = struct.unpack('!H', data[:2])
            data = data[2:]
            output['Sample'] = TS
        # UTC time
        if settings & OutputSettings.Timestamp_UTCTime:
            o = {}
            o['ns'], o['Year'], o['Month'], o['Day'], o['Hour'],\
                o['Minute'], o['Second'], o['Flags'] = struct.unpack(
                    '!ihbbbbb', data[:12])
            data = data[12:]
            output['Timestamp'] = o
        # TODO at that point data should be empty
    except struct.error, e:
        raise MTException("could not parse MTData message.")
    if data != '':
        raise MTException("could not parse MTData message (too long).")
    return output

def get_output_config(config_arg):
    """Parse the mark IV output configuration argument."""
    # code and max frequency
    #
    code_dict = {
        'tt': (0x0810, 1),
        'iu': (0x1010, 2000),
        'ip': (0x1020, 2000),
        'ii': (0x1030, 2000),
        'if': (0x1060, 2000),
        'ic': (0x1070, 2000),
        'ir': (0x1080, 2000),
        'oq': (0x2010, 400),
        'om': (0x2020, 400),
        'oe': (0x2030, 400),
        'bp': (0x3010, 50),
        'ad': (0x4010, 2000),
        'aa': (0x4020, 2000),
        'af': (0x4030, 2000),
        'ah': (0x4040, 1000),
        'pa': (0x5020, 400),
        'pp': (0x5030, 400),
        'pl': (0x5040, 400),
        'np': (0x7010, 4),
        'ns': (0x7020, 4),
        'wr': (0x8020, 2000),
        'wd': (0x8030, 2000),
        'wh': (0x8040, 1000),
        'gd': (0x8830, 4),
        'gs': (0x8840, 4),
        'gu': (0x8880, 4),
        'gi': (0x88A0, 4),
        'rr': (0xA010, 2000),
        'rt': (0xA020, 2000),
        'mf': (0xC020, 100),
        'vv': (0xD010, 400),
        'sb': (0xE010, 2000),
        'sw': (0xE020, 2000)
    }
    # format flags
    format_dict = {'f': 0x00, 'd': 0x03, 'e': 0x00, 'n': 0x04, 'w': 0x08}
    config_re = re.compile('([a-z]{2})(\d+)?([fdenw])?([fdnew])?')
    output_configuration = []
    try:
        for item in config_arg.split(','):
            group, frequency, fmt1, fmt2 = config_re.findall(item.lower())[0]
            code, max_freq = code_dict[group]
            if fmt1 in format_dict:
                code |= format_dict[fmt1]
            if fmt2 in format_dict:
                code |= format_dict[fmt2]
            if frequency:
                frequency = min(max_freq, int(frequency))
            else:
                frequency = max_freq
            output_configuration.append((code, frequency))
        return output_configuration
    except (IndexError, KeyError):
        print 'could not parse output specification "%s"' % item
        return

def pedirIDDispositivo(ser):
    ser.write('0xFA 0xFF 0x00 0x00 0x01')


# INICIO EJECUCION

global ser

#logging.basicConfig(filename='logs/hiloIMU.log',format='HiloIMU - %(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logging.basicConfig(filename='/media/card/logs/hiloIMU.log',format='HiloIMU - %(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)

try:
    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1, writeTimeout=1)
except IOError, e:
    #print("HILOIMU: ERROR >>> AL ABRIR LA COMUNICACION CON LA IMU >>>> "+ str(e))
    #print("Intentando por segunda vez...")
    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1,
                                        writeTimeout=1, rtscts=True,
                                        dsrdtr=True)
atexit.register(finalizar)

try:
    if not ser.isOpen():
        print("HILOIMU: Unable to open serial port!")
        logging.error("No es posible abrir el serial para la IMU.")
        raise SystemExit

    print("Inicializando IMU...")
    envioBajoNivel(ser, MID.GoToConfig)
    leerBajoNivel(ser)

    #almacenamientoRedis = redis.StrictRedis(host='localhost', port=6379, db=0)
    output_configuration = get_output_config("oe100fe,bp50,aa100fe,wr100fe,mf100fe")
    data = b''.join(struct.pack('!HH', *output)
                            for output in output_configuration)
    envioBajoNivel(ser, MID.SetOutputConfiguration, data)
    leerBajoNivel(ser)
except Exception:
        print("Error en la lectura de la IMU: desenchufa la IMU")
        logging.error("Error en la lectura de la IMU: ", sys.exc_info()[0])
        sys.exit(1)
'''
determinarModoOutput(ser, OutputMode.Calib)
determinarPeriodo(ser, 1152)
determinarSkipFactor(ser, 0)
tiempoRedis = almacenamientoRedis.get("tiempo")
tiempo = None
if(tiempoRedis != ''):
    tiempo = json.loads(tiempoRedis)
else:
    tiempo = ''

if(tiempo != ''):
    print(int(tiempo['ano']))
    print(int(tiempo['mes']))
    print(int(tiempo['dia']))
    print(tiempo)
    print(tiempo['UTC'][7:9]+" , "+tiempo['UTC'][:2]+" , "+tiempo['UTC'][2:4]+" , "+ tiempo['UTC'][4:6])
    determinarTiempoUTC(ser, int(tiempo['UTC'][7:9])*1000, int(tiempo['ano']), int(tiempo['mes']), int(tiempo['dia']), int(tiempo['UTC'][:2]), int(tiempo['UTC'][2:4]), int(tiempo['UTC'][4:6]), 1)
else:
    momento = datetime.utcnow()
    determinarTiempoUTC(ser, momento.microsecond*1000, momento.year, momento.month, momento.day, momento.hour, momento.minute, momento.second, 1)

#print(obtenerConfiguracion(ser))
#print("HILOIMU: ------------------------------------")
envioBajoNivel(ser, MID.GoToMeasurement)
mid, data = leerBajoNivel(ser)


while True:
    info =leerValores(ser)
    push_element = almacenamientoRedis.lpush('cola_imu', json.dumps(info))
    #unpacked_images = json.loads(r.get('images'))
    tiempoActual = time.strftime("%d%m%y_%H%M%S", time.localtime())
    nombreFichero = '/media/card/imu_'+ tiempoActual +'.txt'
    fichero = open(nombreFichero, "wb")
    fichero.write(str(info))
    fichero.close()
'''
obtenerConfiguracion(ser)

envioBajoNivel(ser, MID.GoToMeasurement)
leerBajoNivel(ser)
leerBajoNivel(ser)

while True:
    try:
        info =leerValores(ser)
    except Exception as e:
        print("Error en la lectura de la IMU: desenchufa la IMU ("+ str(e)+")")
        logging.error("Error en la lectura de la IMU: "+ str(e))
    #print("IMU:")
    #print(info)
    try:
        if(info != None):
            if ("Orientation Data" in info) and ("Acceleration" in info):
                if('Pressure' in info):
                    #print(info)
                    info['Barometro'] = info['Pressure']['Pressure']
                    print(json.dumps(info))
                else:
                    info['Barometro'] = 0
                    print(json.dumps(info))
                logging.info('Correcto enviado IMU')
            else:
                logging.error("La IMU no esta devolviendo Orientation Data o Acceleration")
        else:
            logging.error("La IMU esta devolviendo NONE.")
    except:
        print("Error en el hiloIMU.")
        logging.error("Error en la IMU.")
