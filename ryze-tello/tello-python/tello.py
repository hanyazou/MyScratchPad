import threading 
import socket
import time
import sys

class Tello:
    def __init__(self):
        self.debug = False
        self.cmd = None
        self.command('command')
        threading.Thread(target=self.thread).start()

    def command(self, cmd, repeat = True):
        if self.debug:
            print ('Tello.command(cmd=%s)' % cmd)
        if self.cmd != 'command' or cmd == 'quit':
            self.cmd = cmd
            self.repeat = repeat
        else:
            print ('Tello.command(cmd=%s): not ready' % cmd)

    def disableRepeat(self):
        if self.cmd != 'command':
            self.repeat = False

    def thread(self):
        # Create a UDP socket
        tello_addr = ('192.168.10.1', 8889)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        local_ddr = ('', 9000)
        sock.bind(local_ddr)
        sock.settimeout(3.0)

        while self.cmd != 'quit':
            cmd = self.cmd
            if self.debug:
                print ('Tello.thread(cmd=%s)' % cmd)
            if cmd == '' or cmd == None:
                time.sleep(0.01)
            else:
                try:
                    # Send data
                    if not self.debug:
                        sent = sock.sendto(cmd, tello_addr)
                except KeyboardInterrupt, e:
                    print('send: command=' + cmd + ': ')
                    print(e)
                    exit(1)
                except Exception, e:
                    print('send: command=' + cmd + ': ')
                    print(e)
                    time.sleep(3.0)
                    continue

                try:
                    if not self.debug:
                        data, server = sock.recvfrom(1518)
                    else:
                        data = 'OK'
                    print ('command: ' + cmd + ': ' + data)
                except socket.timeout, e:
                    print ('recv: cmd=' + cmd + ': timeout')
                    data = None
                except Exception, e:
                    print ('recv: cmd=' + cmd + ': ')
                    print(e)
                    data = None
                if self.cmd == 'command' and data == 'OK':
                    print('\nREADY\n')
                    self.cmd = None
                if not self.repeat:
                    print('end of command repeat: cmd=' + self.cmd)
                    self.cmd = None
                if data != 'OK':
                    time.sleep(0.2)

        print ('tello: exit from the thread.')
