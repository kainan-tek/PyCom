import logging
import os
import time

LogInfo = {"win_tmp": r"C:/temp",
           "dbg_reldir": r"log/pycom/debug"
           }


class Log:
    def __init__(self):
        if "nt" in os.name:
            dbg_dirname = os.path.normpath(os.path.join(LogInfo["win_tmp"], LogInfo["dbg_reldir"]))
        else:
            dbg_dirname = os.path.join(os.path.expanduser('~'), LogInfo["dbg_reldir"])
        if not os.path.exists(dbg_dirname):
            os.makedirs(dbg_dirname, exist_ok=True)

        time_now = time.strftime("%Y-%m-%d--%H-%M-%S")
        self.logname = os.path.normpath(os.path.join(dbg_dirname, f'{time_now}.log'))

    def __printconsole(self, level, message):
        # 创建一个logger
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        # 创建一个handler，用于写入日志文件
        fh = logging.FileHandler(self.logname, 'a', encoding='utf-8')
        # fh = logging.handlers.TimedRotatingFileHandler(
        #     filename=self.logname, when='D', interval=1, backupCount=10, encoding='utf-8')
        # fh.suffix = "%Y%m%d-%H%M.log"
        fh.setLevel(logging.DEBUG)

        # 再创建一个handler，用于输出到控制台
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # 定义handler的输出格式
        formatter = logging.Formatter('[%(asctime)s] - %(filename)s [Line:%(lineno)d] - [%(levelname)s] - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        # 给logger添加handler
        logger.addHandler(fh)
        logger.addHandler(ch)

        # 记录一条日志
        if level == 'info':
            logger.info(message)
        elif level == 'debug':
            logger.debug(message)
        elif level == 'warning':
            logger.warning(message)
        elif level == 'error':
            logger.error(message)

        # 记录完日志移除句柄Handler
        logger.removeHandler(ch)
        logger.removeHandler(fh)

        # 关闭打开的文件
        fh.close()

    def debug(self, message):
        self.__printconsole('debug', message)

    def info(self, message):
        self.__printconsole('info', message)

    def warning(self, message):
        self.__printconsole('warning', message)

    def error(self, message):
        self.__printconsole('error', message)


log_instance = Log()

if __name__ == "__main__":
    log = Log()
    log.info("test")
