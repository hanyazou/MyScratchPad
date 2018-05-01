import threading 
import socket
import time
import sys

import crc

START_OF_PACKET = 0xcc
WIFI_MSG = 0x1a
VIDEO_RATE_QUERY = 40
LIGHT_MSG = 53
FLIGHT_MSG = 0x56
LOG_MSG = 0x1050

VIDEO_ENCODE_RATE_CMD = 0x20
VIDEO_START_CMD = 0x25
EXPOSURE_CMD = 0x34
TIME_CMD = 70
STICK_CMD = 80
TAKEOFF_CMD = 0x0054
LAND_CMD = 0x0055
FLIP_CMD = 0x005c
QUIT_CMD = 0x00ff

def little16(d):
    return (d&0xff), ((d >> 8)&0xff)

def int16(d0, d1):
    return ((d0&0xff) | ((d1&0xff) << 8))

def byteToHexstring(s):
    if isinstance(s, str):
        return ''.join( [ "%02x " % ord(x) for x in s ] ).strip()
    else:
        return ''.join( [ "%02x " % ord(chr(x)) for x in s ] ).strip()

class Packet:
    def __init__(self, cmd, type = 0x68):
	self.buf = bytearray([
            chr(START_OF_PACKET),
            0, 0,
            0,
            chr(type),
            chr(cmd & 0xff), chr((cmd >> 8)&0xff),
            0, 0])

    def getBuffer(self):
        return self.buf

    def getData(self):
        return self.buf[9:len(buf)-2]

    def addByte(self, d):
        self.buf.append(d)

    def addLittle16(self, d):
        self.buf.append(d&0xff)
        self.buf.append((d>>8)&0xff)

class FlightData:
    def __init__(self, data):
        self.batteryLow = 0
        self.batteryLower = 0
        self.batteryPercentage = 0
        self.batteryState = 0
        self.cameraState = 0
        self.downVisualState = 0
        self.droneBatteryLeft = 0
        self.droneFlyTimeLeft = 0
        self.droneHover = 0
        self.eMOpen = 0
        self.eMSky = 0
        self.eMGround = 0
        self.eastSpeed = 0
        self.electricalMachineryState = 0
        self.factoryMode = 0
        self.flyMode = 0
        self.flySpeed = 0
        self.flyTime = 0
        self.frontIn = 0
        self.frontLSC = 0
        self.frontOut = 0
        self.gravityState = 0
        self.groundSpeed = 0
        self.height = 0
        self.imuCalibrationState = 0
        self.imuState = 0
        self.lightStrength = 0
        self.northSpeed = 0
        self.outageRecording = 0
        self.powerState = 0
        self.pressureState = 0
        self.smartVideoExitMode = 0
        self.temperatureHeight = 0
        self.throwFlyTimer = 0
        self.wifiDisturb = 0
        self.wifiStrength = 0
        self.windState = 0

	if len(data) < 24:
            return

        self.height      = int16(data[0], data[1])
        self.northSpeed  = int16(data[2], data[3])
        self.eastSpeed   = int16(data[4], data[5])
        self.groundSpeed = int16(data[6], data[7])
        self.flyTime     = int16(data[8], data[9])

	self.imuState        = ((data[10] >> 0) & 0x1)
	self.pressureState   = ((data[10] >> 1) & 0x1)
	self.downVisualState = ((data[10] >> 2) & 0x1)
	self.powerState      = ((data[10] >> 3) & 0x1)
	self.batteryState    = ((data[10] >> 4) & 0x1)
	self.gravityState    = ((data[10] >> 5) & 0x1)
	self.windState       = ((data[10] >> 7) & 0x1)

        self.imuCalibrationState = data[11]
        self.batteryPercentage = data[12]
        self.droneBatteryLeft = int16(data[13], data[14])
        self.droneFlyTimeLeft = int16(data[15], data[16])

        self.eMSky           = ((data[17] >> 0) & 0x1)
        self.eMGround        = ((data[17] >> 1) & 0x1)
        self.eMOpen          = ((data[17] >> 2) & 0x1)
        self.droneHover      = ((data[17] >> 3) & 0x1)
        self.outageRecording = ((data[17] >> 4) & 0x1)
        self.batteryLow      = ((data[17] >> 5) & 0x1)
        self.batteryLower    = ((data[17] >> 6) & 0x1)
        self.factoryMode     = ((data[17] >> 7) & 0x1)

        self.flyMode       = data[18]
        self.throwFlyTimer = data[19]
        self.cameraState   = data[20]
        self.electricalMachineryState = data[21]

        self.frontIn = ((data[22] >> 0) & 0x1)
        self.frontOut = ((data[22] >> 1) & 0x1)
        self.frontLSC = ((data[22] >> 2) & 0x1)

        self.temperatureHeight = ((data[23] >> 0) & 0x1)

    def __str__(self):
        return (
            ("height %04x\n" % self.height) +
            ("batteryPercentage: %02x\n" % self.batteryPercentage) +
            ("droneBatteryLeft: %04x\n" % self.droneBatteryLeft) +
            "")

class Drone:
    def __init__(self):
        self.tello_addr = ('192.168.10.1', 8889)
        self.debug = False
        self.cmd = None
        self.pkt_seq_num = 0x01e4
        threading.Thread(target=self.thread).start()

    def takeoff(self):
        if self.debug:
            print ('tello: takemoff (cmd=%02x)' % TAKEOFF_CMD)
        pkt = Packet(TAKEOFF_CMD)
        self.enqueuePacket(pkt)

    def land(self):
        if self.debug:
            print ('tello: land (cmd=%02x)' % LAND_CMD)
        pkt = Packet(LAND_CMD)
        pkt.addByte(0x00)
        self.enqueuePacket(pkt)

    def quit(self):
        if self.debug:
            print ('tello: land (cmd=QUIT)')
        pkt = Packet(QUIT_CMD)
        self.enqueuePacket(pkt)

    def enqueuePacket(self, pkt):
        buf = pkt.getBuffer()
        buf[1], buf[2] = little16(len(buf)+2)
        buf[1] = (buf[1] << 3)
        buf[3] = crc.crc8(buf[0:3])
        buf[7], buf[8] = little16(self.pkt_seq_num)
        self.pkt_seq_num = self.pkt_seq_num + 1
        pkt.addLittle16(crc.crc16(buf))
        if self.debug:
            print "tello: enqueue: %s" % byteToHexstring(buf)
        self.cmd = pkt

    def thread(self):
        # Create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        local_ddr = ('', 9000)
        sock.bind(local_ddr)
        sock.settimeout(3.0)

        sock.sendto("conn_req:\x96\x17", self.tello_addr)

        while True:
            if self.cmd:
                cmd = self.cmd.getBuffer()
                if self.debug:
                    print ("tello: dequeue: %s" % byteToHexstring(cmd))
            else:
                cmd = None

            if cmd != None:
                if (cmd[5] | (cmd[6]<<8)) == QUIT_CMD:
                    break
                try:
                    # Send data
                    sent = sock.sendto(cmd, self.tello_addr)
                    if self.debug:
                        print ("tello:    send: %s" % byteToHexstring(cmd))
                    self.cmd = None
                    if self.debug:
                        print ("tello: self.cmd = None")
                except KeyboardInterrupt, e:
                    print("tello:    send: %s: " % byteToHexstring(cmd))
                    print(e)
                    exit(1)
                except Exception, e:
                    print("tello:    send: %s: " % byteToHexstring(cmd))
                    print(e)
                    time.sleep(3.0)
                    continue

            try:
                data, server = sock.recvfrom(1518)
                if self.debug:
                    print ("tello:recv1518: %s" % byteToHexstring(data))
                data, server = sock.recvfrom(9617)
                if self.debug:
                    print ("tello:recv9617: %s" % byteToHexstring(data))
            except socket.timeout, e:
                print ('tello:    recv: timeout')
                data = None
            except Exception, e:
                print ('tello:    recv: ')
                print(e)
                data = None
            if data != None:
                data = bytearray([x for x in data])
                if data[0] != START_OF_PACKET:
                    print('start of packet != %02x (%02x) (ignored)' % (START_OF_PACKET, data[0]))
                    continue
                cmd = int16(data[5], data[6])
                if cmd == LOG_MSG:
                    print ("tello:    recv: LOG")
                elif cmd == WIFI_MSG:
                    print ("tello:    recv: WIFI")
                elif cmd == LIGHT_MSG:
                    print ("tello:    recv: LIGHT")
                elif cmd == FLIGHT_MSG:
                    print ("tello:    recv: FLIGHT")
                    flight_data = FlightData(data[9:])
                    print flight_data
                else:
                    print('unknown packet id = %04x (ignored)' % cmd)

        print ('tello: exit from the thread.')

if __name__ == '__main__':
    d = Drone()
    d.land()
    time.sleep(5)
    d.takeoff()
    time.sleep(10)
    d.land()
    time.sleep(5)
    d.quit()
