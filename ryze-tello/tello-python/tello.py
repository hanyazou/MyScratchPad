import threading
import socket
import time
import datetime
import sys
import traceback
import louie.dispatcher as dispatcher

import crc
import logger
import event

log = logger.Logger('Tello')

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


def little16(val):
    return (val & 0xff), ((val >> 8) & 0xff)


def int16(val0, val1):
    return (val0 & 0xff) | ((val1 & 0xff) << 8)


def byte_to_hexstring(buf):
    if isinstance(buf, str):
        return ''.join(["%02x " % ord(x) for x in buf]).strip()

    return ''.join(["%02x " % ord(chr(x)) for x in buf]).strip()


def show_exception(ex):
    log.error(str(ex))
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback.print_exception(exc_type, exc_value, exc_traceback)


class Packet(object):
    def __init__(self, cmd, pkt_type=0x68):
        if isinstance(cmd, (bytearray, str)):
            self.buf = bytearray()
            self.buf[:] = cmd
        else:
            self.buf = bytearray([
                chr(START_OF_PACKET),
                0, 0,
                0,
                chr(pkt_type),
                chr(cmd & 0xff), chr((cmd >> 8) & 0xff),
                0, 0])

    def get_buffer(self):
        return self.buf

    def get_data(self):
        return self.buf[9:len(self.buf)-2]

    def add_byte(self, val):
        self.buf.append(val & 0xff)

    def add_int16(self, val):
        self.add_byte(val)
        self.add_byte(val >> 8)

    def add_time(self, time=datetime.datetime.now()):
        self.add_byte(0)
        self.add_int16(time.hour)
        self.add_int16(time.minute)
        self.add_int16(time.second)
        self.add_int16((time.microsecond/1000) & 0xff)
        self.add_int16(((time.microsecond/1000) >> 8) & 0xff)


class FlightData(object):
    def __init__(self, data):
        self.battery_low = 0
        self.battery_lower = 0
        self.battery_percentage = 0
        self.battery_state = 0
        self.camera_state = 0
        self.down_visual_state = 0
        self.drone_battery_left = 0
        self.drone_fly_time_left = 0
        self.drone_hover = 0
        self.em_open = 0
        self.em_sky = 0
        self.em_ground = 0
        self.east_speed = 0
        self.electrical_machinery_state = 0
        self.factory_mode = 0
        self.fly_mode = 0
        self.fly_speed = 0
        self.fly_time = 0
        self.front_in = 0
        self.front_lsc = 0
        self.front_out = 0
        self.gravity_state = 0
        self.ground_speed = 0
        self.height = 0
        self.imu_calibration_state = 0
        self.imu_state = 0
        self.light_strength = 0
        self.north_speed = 0
        self.outage_recording = 0
        self.power_state = 0
        self.pressure_state = 0
        self.smart_video_exit_mode = 0
        self.temperature_height = 0
        self.throw_fly_timer = 0
        self.wifi_disturb = 0
        self.wifi_strength = 0
        self.wind_state = 0

        if len(data) < 24:
            return

        self.height = int16(data[0], data[1])
        self.north_speed = int16(data[2], data[3])
        self.east_speed = int16(data[4], data[5])
        self.ground_speed = int16(data[6], data[7])
        self.fly_time = int16(data[8], data[9])

        self.imu_state = ((data[10] >> 0) & 0x1)
        self.pressure_state = ((data[10] >> 1) & 0x1)
        self.down_visual_state = ((data[10] >> 2) & 0x1)
        self.power_state = ((data[10] >> 3) & 0x1)
        self.battery_state = ((data[10] >> 4) & 0x1)
        self.gravity_state = ((data[10] >> 5) & 0x1)
        self.wind_state = ((data[10] >> 7) & 0x1)

        self.imu_calibration_state = data[11]
        self.battery_percentage = data[12]
        self.drone_battery_left = int16(data[13], data[14])
        self.drone_fly_time_left = int16(data[15], data[16])

        self.em_sky = ((data[17] >> 0) & 0x1)
        self.em_ground = ((data[17] >> 1) & 0x1)
        self.em_open = ((data[17] >> 2) & 0x1)
        self.drone_hover = ((data[17] >> 3) & 0x1)
        self.outage_recording = ((data[17] >> 4) & 0x1)
        self.battery_low = ((data[17] >> 5) & 0x1)
        self.battery_lower = ((data[17] >> 6) & 0x1)
        self.factory_mode = ((data[17] >> 7) & 0x1)

        self.fly_mode = data[18]
        self.throw_fly_timer = data[19]
        self.camera_state = data[20]
        self.electrical_machinery_state = data[21]

        self.front_in = ((data[22] >> 0) & 0x1)
        self.front_out = ((data[22] >> 1) & 0x1)
        self.front_lsc = ((data[22] >> 2) & 0x1)

        self.temperature_height = ((data[23] >> 0) & 0x1)

    def __str__(self):
        return (
            ("height=%04x" % self.height) +
            (", battery_percentage=%02x" % self.battery_percentage) +
            (", drone_battery_left=%04x" % self.drone_battery_left) +
            "")


class Drone(object):
    CONNECTED_EVENT = event.Event('connected')
    WIFI_EVENT = event.Event('wifi')
    LIGHT_EVENT = event.Event('light')
    FLIGHT_EVENT = event.Event('fligt')
    LOG_EVENT = event.Event('log')

    LOG_ERROR = logger.LOG_ERROR
    LOG_WARN = logger.LOG_WARN
    LOG_INFO = logger.LOG_INFO
    LOG_DEBUG = logger.LOG_DEBUG
    LOG_ALL = logger.LOG_ALL

    def __init__(self, port=9617):
        self.tello_addr = ('192.168.10.1', 8889)
        self.debug = False
        self.cmd = None
        self.pkt_seq_num = 0x01e4
        self.port = port
        threading.Thread(target=self.thread).start()

    def set_loglevel(self, level):
        log.set_level(level)

    def connect(self):
        port = self.port
        port0 = ((port/1000) % 10) << 4 | ((port/100) % 10)
        port1 = ((port/10) % 10) << 4 | ((port/1) % 10)
        buf = 'conn_req:%c%c' % (chr(port0), chr(port1))
        log.info('connect (cmd="%s")' % str(buf))
        self.enqueue_packet(Packet(buf))

    def subscribe(self, signal, handler):
        dispatcher.connect(handler, signal, sender=self)

    def publish(self, event, **args):
        args.update({'event': event, 'port': self.port})
        log.debug('publish signal=%s, args=%s' % (event, args))
        dispatcher.send(signal=event, sender=self, **args)

    def takeoff(self):
        log.info('takemoff (cmd=0x%02x)' % TAKEOFF_CMD)
        pkt = Packet(TAKEOFF_CMD)
        self.enqueue_packet(pkt)

    def land(self):
        log.info('land (cmd=0x%02x)' % LAND_CMD)
        pkt = Packet(LAND_CMD)
        pkt.add_byte(0x00)
        self.enqueue_packet(pkt)

    def quit(self):
        log.info('quit (cmd=QUIT)')
        pkt = Packet(QUIT_CMD)
        self.enqueue_packet(pkt)

    def send_time(self):
        log.info('send_time (cmd=0x%02x)' % TIME_CMD)
        pkt = Packet(TIME_CMD, 0x50)
        pkt.add_time()
        self.enqueue_packet(pkt)

    def enqueue_packet(self, pkt):
        buf = pkt.get_buffer()
        if buf[0] == START_OF_PACKET:
            buf[1], buf[2] = little16(len(buf)+2)
            buf[1] = (buf[1] << 3)
            buf[3] = crc.crc8(buf[0:3])
            buf[7], buf[8] = little16(self.pkt_seq_num)
            self.pkt_seq_num = self.pkt_seq_num + 1
            pkt.add_int16(crc.crc16(buf))
        log.debug("tello: enqueue: %s" % byte_to_hexstring(buf))
        self.cmd = pkt

    def process_packet(self, data):
        if isinstance(data, str):
            data = bytearray([x for x in data])
        if str(data[0:9]) == 'conn_ack:':
            log.info('connected. (port=%2x%2x)' % (data[9], data[10]))
            log.debug('    %s' % byte_to_hexstring(data))
            self.publish(event=self.CONNECTED_EVENT, data=data)
            return True
        if data[0] != START_OF_PACKET:
            log.info('start of packet != %02x (%02x) (ignored)' % (START_OF_PACKET, data[0]))
            log.info('    %s' % byte_to_hexstring(data))
            log.info('    %s' % str(map(chr, data))[1:-1])
            return False

        cmd = int16(data[5], data[6])
        if cmd == LOG_MSG:
            log.debug("recv: log: %s" % byte_to_hexstring(data[9:]))
            self.publish(event=self.LOG_EVENT, data=data[9:])
        elif cmd == WIFI_MSG:
            log.debug("recv: wifi: %s" % byte_to_hexstring(data[9:]))
            self.publish(event=self.WIFI_EVENT, data=data[9:])
        elif cmd == LIGHT_MSG:
            log.debug("recv: light: %s" % byte_to_hexstring(data[9:]))
            self.publish(event=self.LIGHT_EVENT, data=data[9:])
        elif cmd == FLIGHT_MSG:
            flight_data = FlightData(data[9:])
            log.debug("recv: flight data: %s" % str(flight_data))
            self.publish(event=self.FLIGHT_EVENT, data=flight_data)
        else:
            log.info('unknown packet: %s' % byte_to_hexstring(data))
            return False

        return True

    def thread(self):
        # Create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        local_ddr = ('', 9000)
        sock.bind(local_ddr)
        sock.settimeout(3.0)

        while True:
            if self.cmd:
                cmd = self.cmd.get_buffer()
                log.debug("dequeue: %s" % byte_to_hexstring(cmd))
            else:
                cmd = None

            if cmd is not None:
                if (cmd[5] | (cmd[6] << 8)) == QUIT_CMD:
                    break
                try:
                    # Send data
                    sent = sock.sendto(cmd, self.tello_addr)
                    log.debug("   send: %s" % byte_to_hexstring(cmd))
                    self.cmd = None
                    log.debug("self.cmd = None")
                except KeyboardInterrupt, ex:
                    show_exception(ex)
                    exit(1)
                except Exception, ex:
                    log.error("   send: %s: " % byte_to_hexstring(cmd))
                    show_exception(ex)
                    time.sleep(3.0)
                    continue

            try:
                data, server = sock.recvfrom(1518)
                log.debug("recv(1518): %s" % byte_to_hexstring(data))
                self.process_packet(data)
                data, server = sock.recvfrom(self.port)
                log.debug("recv(%s): %s" % (self.port, byte_to_hexstring(data)))
                self.process_packet(data)
            except socket.timeout, ex:
                log.error('   recv: timeout')
                data = None
            except Exception, ex:
                log.error('   recv: ')
                show_exception(ex)

        log.info('exit from the thread.')

if __name__ == '__main__':
    def handler(event, sender, data, **args):
        print 'event="%s" data=%s' % (event.getname(), str(data))

    d = Drone()
    try:
        # d.set_loglevel(d.LOG_ALL)
        d.subscribe(d.CONNECTED_EVENT, handler)
        # d.subscribe(d.WIFI_EVENT, handler)
        # d.subscribe(d.LIGHT_EVENT, handler)
        d.subscribe(d.FLIGHT_EVENT, handler)
        # d.subscribe(d.LOG_EVENT, handler)

        d.connect()
        time.sleep(2)
        d.send_time()
        # d.takeoff()
        time.sleep(5)
        d.land()
        time.sleep(5)
    except Exception, ex:
        show_exception(ex)
    finally:
        d.quit()
