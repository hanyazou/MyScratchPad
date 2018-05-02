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
import error

log = logger.Logger('Tello')

START_OF_PACKET = 0xcc
WIFI_MSG = 0x1a
VIDEO_RATE_QUERY = 40
LIGHT_MSG = 53
FLIGHT_MSG = 0x56
LOG_MSG = 0x1050

VIDEO_ENCODER_RATE_CMD = 0x20
VIDEO_START_CMD = 0x25
EXPOSURE_CMD = 0x34
TIME_CMD = 70
STICK_CMD = 80
TAKEOFF_CMD = 0x0054
LAND_CMD = 0x0055
FLIP_CMD = 0x005c


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

    def fixup(self, seq_num=0):
        buf = self.get_buffer()
        if buf[0] == START_OF_PACKET:
            buf[1], buf[2] = little16(len(buf)+2)
            buf[1] = (buf[1] << 3)
            buf[3] = crc.crc8(buf[0:3])
            buf[7], buf[8] = little16(seq_num)
            self.add_int16(crc.crc16(buf))

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
        self.add_int16(time.hour)
        self.add_int16(time.minute)
        self.add_int16(time.second)
        self.add_int16((time.microsecond/1000) & 0xff)
        self.add_int16(((time.microsecond/1000) >> 8) & 0xff)

    def get_time(self, buf=None):
        if buf is None:
            buf = self.get_data()[1:]
        hour = int16(buf[0], buf[1])
        min = int16(buf[2], buf[3])
        sec = int16(buf[4], buf[5])
        millisec = int16(buf[6], buf[8])
        now = datetime.datetime.now()
        return datetime.datetime(now.year, now.month, now.day, hour, min, sec, millisec)


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
            ("height=%2d" % self.height) +
            (", fly_mode=0x%02x" % self.fly_mode) +
            (", battery_percentage=%2d" % self.battery_percentage) +
            (", drone_battery_left=0x%04x" % self.drone_battery_left) +
            "")


class Drone(object):
    CONNECTED_EVENT = event.Event('connected')
    WIFI_EVENT = event.Event('wifi')
    LIGHT_EVENT = event.Event('light')
    FLIGHT_EVENT = event.Event('fligt')
    LOG_EVENT = event.Event('log')
    TIME_EVENT = event.Event('time')
    VIDEO_FRAME_EVENT = event.Event('video frame')

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
        self.udpsize = 2000
        self.left_x = 0.0
        self.left_y = 0.0
        self.right_x = 0.0
        self.right_y = 0.0
        self.sock = None
        self.running = True
        threading.Thread(target=self.recv_thread).start()
        threading.Thread(target=self.video_thread).start()

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
        log.info('takemoff (cmd=0x%02x seq=0x%04x)' % (TAKEOFF_CMD, self.pkt_seq_num))
        pkt = Packet(TAKEOFF_CMD)
        self.enqueue_packet(pkt)

    def land(self):
        log.info('land (cmd=0x%02x seq=0x%04x)' % (LAND_CMD, self.pkt_seq_num))
        pkt = Packet(LAND_CMD)
        pkt.add_byte(0x00)
        self.enqueue_packet(pkt)

    def quit(self):
        log.info('quit')
        self.running = False

    def __prepare_time_command(self):
        log.info('send_time (cmd=0x%02x seq=0x%04x)' % (TIME_CMD, self.pkt_seq_num))
        pkt = Packet(TIME_CMD, 0x50)
        pkt.add_byte(0)
        pkt.add_time()
        return pkt

    def start_video(self):
        """start_video tells Tello to send start info (SPS/PPS) for video stream."""
        log.info('start video (cmd=0x%02x seq=0x%04x)' % (VIDEO_START_CMD, self.pkt_seq_num))
        pkt = Packet(VIDEO_START_CMD, 0x60)
        pkt.fixup()
        return self.send_packet(pkt)

    def set_exposure(self, level):
        """set_exposure sets the drone camera exposure level. Valid levels are 0, 1, and 2."""
        if level < 0 or 2 < level:
            raise error.TelloError('Invalid exposure level')
        log.info('set exposure (cmd=0x%02x seq=0x%04x)' % (EXPOSURE_CMD, self.pkt_seq_num))
        pkt = Packet(EXPOSURE_CMD, 0x48)
        pkt.add_byte(level)
        pkt.fixup()
        return self.send_packet(pkt)

    def set_video_encoder_rate(self, rate):
        """set_video_encoder_rate sets the drone video encoder rate."""
        log.info('set video encoder rate (cmd=0x%02x seq=%04x)' %
                 (VIDEO_ENCODER_RATE_CMD, self.pkt_seq_num))
        pkt = Packet(VIDEO_ENCODER_RATE_CMD, 0x68)
        pkt.add_byte(rate)
        pkt.fixup()
        return self.send_packet(pkt)

    def up(self, val):
        """Up tells the drone to ascend. Pass in an int from 0-100."""
        log.info('up(val=%d)' % val)
        self.left_y = val / 100.0

    def down(self, val):
        """Down tells the drone to descend. Pass in an int from 0-100."""
        log.info('down(val=%d)' % val)
        self.left_y = val / 100.0 * -1

    def forward(self, val):
        """Forward tells the drone to go forward. Pass in an int from 0-100."""
        log.info('forward(val=%d)' % val)
        self.right_y = val / 100.0

    def backward(self, val):
        """Backward tells drone to go in reverse. Pass in an int from 0-100."""
        log.info('backward(val=%d)' % val)
        self.right_y = val / 100.0 * -1

    def right(self, val):
        """Right tells drone to go right. Pass in an int from 0-100."""
        log.info('right(val=%d)' % val)
        self.right_x = val / 100.0

    def left(self, val):
        """Left tells drone to go left. Pass in an int from 0-100."""
        log.info('left(val=%d)' % val)
        self.right_x = val / 100.0 * -1

    def clockwise(self, val):
        """Clockwise tells drone to rotate in a clockwise direction. Pass in an int from 0-100."""
        log.info('clockwise(val=%d)' % val)
        self.left_x = val / 100.0

    def counter_clockwise(self, val):
        """
        CounterClockwise tells drone to rotate in a counter-clockwise direction.
        Pass in an int from 0-100.
        """
        log.info('counter_clockwise(val=%d)' % val)
        self.left_x = val / 100.0 * -1

    def __fix_range(self, val, min=-1.0, max=1.0):
        if val < min:
            val = min
        elif val > max:
            val = max
        return val

    def set_throttle(self, throttle):
        if self.left_y != self.__fix_range(throttle):
            log.info('set_throttle(val=%4.2f)' % throttle)
        self.left_y = self.__fix_range(throttle)

    def set_yaw(self, yaw):
        if self.left_x != self.__fix_range(yaw):
            log.info('set_yaw(val=%4.2f)' % yaw)
        self.left_x = self.__fix_range(yaw)

    def set_pitch(self, pitch):
        if self.right_y != self.__fix_range(pitch):
            log.info('set_pitch(val=%4.2f)' % pitch)
        self.right_y = self.__fix_range(pitch)

    def set_roll(self, roll):
        if self.right_x != self.__fix_range(roll):
            log.info('set_roll(val=%4.2f)' % roll)
        self.right_x = self.__fix_range(roll)

    def __prepare_stick_command(self):
        pkt = Packet(STICK_CMD, 0x60)

        axis1 = int(1024 + 660.0 * self.right_x) & 0x7ff
        axis2 = int(1024 + 660.0 * self.right_y) & 0x7ff
        axis3 = int(1024 + 660.0 * self.left_y) & 0x7ff
        axis4 = int(1024 + 660.0 * self.left_x) & 0x7ff
        '''
        11 bits (-1024 ~ +1023) x 4 axis = 44 bits
        44 bits will be packed in to 6 bytes (48 bits)

                    axis4      axis3      axis2      axis1
             |          |          |          |          |
                 4         3         2         1         0
        98765432109876543210987654321098765432109876543210
         |       |       |       |       |       |       |
             byte5   byte4   byte3   byte2   byte1   byte0
        '''
        log.debug("stick command: yaw=%4d thr=%4d pit=%4d rol=%4d" %
                  (axis4, axis3, axis2, axis1))
        log.debug("stick command: yaw=%04x thr=%04x pit=%04x rol=%04x" %
                  (axis4, axis3, axis2, axis1))
        pkt.add_byte(((axis2 << 11 | axis1) >> 0) & 0xff)
        pkt.add_byte(((axis2 << 11 | axis1) >> 8) & 0xff)
        pkt.add_byte(((axis3 << 11 | axis2) >> 5) & 0xff)
        pkt.add_byte(((axis4 << 11 | axis3) >> 2) & 0xff)
        pkt.add_byte(((axis4 << 11 | axis3) >> 10) & 0xff)
        pkt.add_byte(((axis4 << 11 | axis3) >> 18) & 0xff)
        pkt.add_time()

        return pkt

    def enqueue_packet(self, pkt):
        pkt.fixup(self.pkt_seq_num)
        self.pkt_seq_num = self.pkt_seq_num + 1
        log.debug("enqueue: %s" % byte_to_hexstring(pkt.get_buffer()))
        self.cmd = pkt

    def send_packet(self, pkt):
        try:
            cmd = pkt.get_buffer()
            self.sock.sendto(cmd, self.tello_addr)
            log.debug("stick command: %s" % byte_to_hexstring(cmd))
        except socket.error as err:
            log.error("send_packet: %s" % str(err))
            return False

        return True

    def process_packet(self, data):
        if isinstance(data, str):
            data = bytearray([x for x in data])

        if str(data[0:9]) == 'conn_ack:':
            log.info('connected. (port=%2x%2x)' % (data[9], data[10]))
            log.debug('    %s' % byte_to_hexstring(data))
            self.publish(event=self.CONNECTED_EVENT, data=data)

            # send time
            pkt = self.__prepare_time_command()
            pkt.fixup()
            self.send_packet(pkt)  # ignore errors
            log.debug("send time command: %s" % byte_to_hexstring(pkt.get_buffer()))

            return True

        if data[0] != START_OF_PACKET:
            log.info('start of packet != %02x (%02x) (ignored)' % (START_OF_PACKET, data[0]))
            log.info('    %s' % byte_to_hexstring(data))
            log.info('    %s' % str(map(chr, data))[1:-1])
            return False

        pkt = Packet(data)
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
        elif cmd == TIME_CMD:
            log.debug("recv: time data: %s" % byte_to_hexstring(data))
            self.publish(event=self.TIME_EVENT, data=data[7:9])
        elif (TAKEOFF_CMD, LAND_CMD, VIDEO_START_CMD, VIDEO_ENCODER_RATE_CMD):
            log.info("recv: ack: cmd=0x%02x seq=0x%04x %s" %
                     (int16(data[5], data[6]), int16(data[7], data[8]), byte_to_hexstring(data)))
        else:
            log.info('unknown packet: %s' % byte_to_hexstring(data))
            return False

        return True

    def recv_thread(self):
        # Create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', 9000))
        sock.settimeout(1.0)
        self.sock = sock

        while self.running:
            if self.cmd:
                cmd = self.cmd.get_buffer()
                log.debug("dequeue: %s" % byte_to_hexstring(cmd))
                if self.send_packet(self.cmd):
                    self.cmd = None
                    log.debug("self.cmd = None")
                else:
                    time.sleep(3.0)
                    continue

            pkt = self.__prepare_stick_command()
            pkt.fixup()
            self.send_packet(pkt)  # ignore errors
            log.debug("stick command: %s" % byte_to_hexstring(pkt.get_buffer()))

            try:
                data, server = sock.recvfrom(self.udpsize)
                log.debug("recv: %s" % byte_to_hexstring(data))
                self.process_packet(data)
            except socket.timeout, ex:
                log.error('recv: timeout')
                data = None
            except Exception, ex:
                log.error('recv: ')
                show_exception(ex)

        log.info('exit from the recv thread.')

    def video_thread(self):
        log.info('start video thread')
        # Create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        port = 6038
        sock.bind(('', port))
        sock.settimeout(1.0)

        while self.running:
            try:
                data, server = sock.recvfrom(self.udpsize)
                log.debug("video recv: %s %d bytes" % (byte_to_hexstring(data[0:2]), len(data)))
                self.publish(event=self.VIDEO_FRAME_EVENT, data=data[2:])
            except socket.timeout, ex:
                log.error('video recv: timeout')
                data = None
            except Exception, ex:
                log.error('video recv: ')
                show_exception(ex)

        log.info('exit from the video thread.')

prev_flight_data = None
prev_video_data_time = None
video_data_size = 0
if __name__ == '__main__':
    def handler(event, sender, data, **args):
        global prev_flight_data
        global prev_video_data_time
        global video_data_size
        if event is Drone.CONNECTED_EVENT:
            print 'connected'
        elif event is Drone.FLIGHT_EVENT:
            if prev_flight_data != str(data):
                print data
                prev_flight_data = str(data)
        elif event is Drone.TIME_EVENT:
            print 'event="%s" data=%d' % (event.getname(), data[0] + data[1] << 8)
        elif event is Drone.VIDEO_FRAME_EVENT:
            now = datetime.datetime.now()
            if prev_video_data_time is None:
                prev_video_data_time = now
            video_data_size += len(data)
            dur = (now - prev_video_data_time).total_seconds()
            if 2.0 < dur:
                print ('event="%s" data %d bytes %5.1fKB/sec' %
                       (event.getname(), video_data_size, video_data_size / dur / 1024))
                video_data_size = 0
                prev_video_data_time = now
        else:
            print 'event="%s" data=%s' % (event.getname(), str(data))

    d = Drone()
    try:
        # d.set_loglevel(d.LOG_ALL)
        d.subscribe(d.CONNECTED_EVENT, handler)
        # d.subscribe(d.WIFI_EVENT, handler)
        # d.subscribe(d.LIGHT_EVENT, handler)
        d.subscribe(d.FLIGHT_EVENT, handler)
        # d.subscribe(d.LOG_EVENT, handler)
        d.subscribe(d.TIME_EVENT, handler)
        d.subscribe(d.VIDEO_FRAME_EVENT, handler)

        d.connect()
        time.sleep(2)
        d.start_video()
        d.set_exposure(0)
        d.set_video_encoder_rate(4)
        d.takeoff()
        time.sleep(5)
        d.down(50)
        time.sleep(3)
        d.up(50)
        time.sleep(3)
        d.down(0)
        time.sleep(2)
        d.land()
        time.sleep(5)
    except Exception, ex:
        show_exception(ex)
    finally:
        d.quit()
    print 'end.'
