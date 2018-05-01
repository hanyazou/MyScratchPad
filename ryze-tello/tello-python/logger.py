import datetime

LOG_ERROR = 0
LOG_WARN = 1
LOG_INFO = 2
LOG_DEBUG = 3
LOG_ALL = 99


class Logger:
    def __init__(self, header=''):
        self.log_level = LOG_INFO
        self.header_string = header

    def header(self):
        now = datetime.datetime.now()
        ts = ("%02d:%02d:%02d.%03d" % (now.hour, now.minute, now.second, now.microsecond/1000))
        return "%s: %s" % (self.header_string, ts)

    def setLevel(self, level):
        self.log_level = level

    def error(self, str):
        if self.log_level < LOG_ERROR:
            return
        print "%s: Error: %s" % (self.header(), str)

    def warn(self, str):
        if self.log_level < LOG_WARN:
            return
        print "%s:  Warn: %s" % (self.header(), str)

    def info(self, str):
        if self.log_level < LOG_INFO:
            return
        print "%s:  Info: %s" % (self.header(), str)

    def debug(self, str):
        if self.log_level < LOG_DEBUG:
            return
        print "%s: Debug: %s" % (self.header(), str)

if __name__ == '__main__':
    log = Logger('test')
    log.error('This is an error message')
    log.warn('This is a warning message')
    log.info('This is an info message')
    log.debug('This should ** NOT **  be displayed')
    log.setLevel(LOG_ALL)
    log.debug('This is a debug message')
