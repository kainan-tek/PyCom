import logging
import os
import time


class Log:
    def __init__(self):
        log_dirname = os.path.join(os.path.expanduser('~'), "log/pycom")
        if not os.path.exists(log_dirname):
            os.makedirs(log_dirname, exist_ok=True)

        time_now = time.strftime("%Y-%m-%d--%H-%M-%S")
        logname = os.path.normpath(os.path.join(log_dirname, f'{time_now}.log'))

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

        fh = logging.FileHandler(logname, 'a', encoding='utf-8')
        # fh = logging.handlers.TimedRotatingFileHandler(
        #     filename=logname, when='D', interval=1, backupCount=10, encoding='utf-8')
        # fh.suffix = "%Y%m%d-%H%M.log"
        fh.setLevel(logging.INFO)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        formatter = logging.Formatter('[%(asctime)s] - %(filename)s [Line:%(lineno)d] - [%(levelname)s] - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

        # logger.removeHandler(ch)
        # logger.removeHandler(fh)
        # fh.close()

    def __print_log(self, level, msg):
        if level == 'info':
            self.logger.info(msg)
        elif level == 'debug':
            self.logger.debug(msg)
        elif level == 'warning':
            self.logger.warning(msg)
        elif level == 'error':
            self.logger.error(msg)

    def debug(self, msg):
        self.__print_log('debug', msg)

    def info(self, msg):
        self.__print_log('info', msg)

    def warning(self, msg):
        self.__print_log('warning', msg)

    def error(self, msg):
        self.__print_log('error', msg)


log_instance = Log()

if __name__ == "__main__":
    log = Log()
    log.info("test")
