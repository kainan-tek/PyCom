import logging
import os
from logging.handlers import RotatingFileHandler

LogInfo = {"reldir": "log/pycom",
           "basename": "pycom.log",
           "filesize": 48*1024*1024,
           "fbkcount": 6
           }


class Log:
    def __init__(self) -> None:
        """
        Initialize the Log class.

        Creates the necessary directory for storing log files, sets up the
        logger, and adds handlers for console and file logging.

        Args:
            None

        Returns:
            None
        """
        log_dirname: str = os.path.join(os.path.expanduser('~'), LogInfo["reldir"])
        if not os.path.exists(log_dirname):
            os.makedirs(log_dirname, exist_ok=True)

        logname: str = os.path.normpath(os.path.join(log_dirname, LogInfo["basename"]))
        formatter: logging.Formatter = logging.Formatter(
            '%(asctime)s - %(filename)s:%(lineno)d - [%(levelname)s] - %(message)s'
        )

        self.logger: logging.Logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

        ch: logging.StreamHandler = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)

        rfh: logging.handlers.RotatingFileHandler = logging.handlers.RotatingFileHandler(
            filename=logname, mode='a', maxBytes=LogInfo["filesize"],
            backupCount=LogInfo["fbkcount"], encoding='utf-8'
        )
        rfh.setLevel(logging.INFO)
        rfh.setFormatter(formatter)

        self.logger.addHandler(ch)
        self.logger.addHandler(rfh)


log_inst = Log()

if __name__ == "__main__":
    # log_inst.logger.debug("test")
    log_inst.logger.info("test")
    # log_inst.logger.warning("test")
    # log_inst.logger.error("test")
    # log_inst.logger.critical("test")
    # log_inst.logger.exception("test")
