import logging
import os
from logging.handlers import RotatingFileHandler

LogInfo = {"reldir": "log/pycom",
           "basename": "pycom.log",
           "filesize": 48*1024*1024,
           "fbkcount": 6
           }


class Log:
    def __init__(self):
        """
        Create a Log instance.

        Initialize the logger and its handlers.
        The logger is the root logger.

        Log to console (StreamHandler) and log file (RotatingFileHandler).
        """
        # Create the directory to store the log file.
        log_dirname = os.path.join(os.path.expanduser('~'), LogInfo["reldir"])
        if not os.path.exists(log_dirname):
            os.makedirs(log_dirname, exist_ok=True)

        # Set the log file name and formatter.
        # Use the normpath function to avoid any potential issues with the '/'
        # character on Windows systems.
        logname = os.path.normpath(os.path.join(log_dirname, LogInfo["basename"]))
        formatter = logging.Formatter('%(asctime)s - %(filename)s:%(lineno)d - [%(levelname)s] - %(message)s')

        # Get the root logger
        self.logger = logging.getLogger()

        # Set the log level
        self.logger.setLevel(logging.DEBUG)

        # Create a StreamHandler to log to console
        ch = logging.StreamHandler()
        # Set the log level for the console handler
        ch.setLevel(logging.INFO)
        # Set the formatter for the console handler
        ch.setFormatter(formatter)

        # Create a RotatingFileHandler to log to file
        rfh = RotatingFileHandler(filename=logname, mode='a',  # file handler
                                  maxBytes=LogInfo["filesize"], backupCount=LogInfo["fbkcount"], encoding='utf-8')
        # Set the log level for the file handler
        rfh.setLevel(logging.INFO)
        # Set the formatter for the file handler
        rfh.setFormatter(formatter)

        # Add the handlers to the logger
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
