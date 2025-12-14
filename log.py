import logging
import sys
from enum import IntEnum
from typing import Optional
from typing import TextIO
from typing import Any


class LogLevel(IntEnum):
    SILENT = 0
    INFO = 1
    DEBUG = 2

APP_LOGGER_NAME = "RALT"

class SimpleLogger:
    def __init__(
        self,
        name: str = APP_LOGGER_NAME,
        level: LogLevel = LogLevel.INFO,
        stream=sys.stdout, # we use stdout by default
        logfile: Optional[str] = None,
    ):
        self._logger = logging.getLogger(name)
        self._logger.propagate = False
        self._logger.handlers.clear()

        self.set_level(level)

        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
        )

        if logfile:
            handler = logging.FileHandler(logfile)
        else:
            handler = logging.StreamHandler(stream)

        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

    # --------------------
    # Compatibility API
    # --------------------

    def set_level(self, level: LogLevel):
        if level == LogLevel.SILENT:
            self._logger.setLevel(logging.CRITICAL + 1)
        elif level == LogLevel.INFO:
            self._logger.setLevel(logging.INFO)
        elif level == LogLevel.DEBUG:
            self._logger.setLevel(logging.DEBUG)

    def debug(self, msg: str):
        self._logger.debug(msg)

    def info(self, msg: str):
        self._logger.info(msg)

    def warn(self, msg: str):
        self._logger.warning(msg)

    def error(self, msg: str):
        self._logger.error(msg)

    # --------------------
    # Advanced escape hatch
    # --------------------
    @property
    def raw(self) -> logging.Logger:
        """Access the underlying logging.Logger"""
        return self._logger


class LogPrinter:
    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def _join(self, *args: Any, sep: str = " ") -> str:
        return sep.join(str(a) for a in args)

    def info(self, *args: Any):
        self._logger.info(self._join(*args))

    def debug(self, *args: Any):
        self._logger.debug(self._join(*args))

    def warn(self, *args: Any):
        self._logger.warning(self._join(*args))

    def error(self, *args: Any):
        self._logger.error(self._join(*args))
    
    def force(self, *args: Any):
        """
        Emit a message regardless of SILENT level.
        """
        record = self._logger.makeRecord(
            name=self._logger.name,
            level=logging.INFO,
            fn="",
            lno=0,
            msg=self._join(*args),
            args=None,
            exc_info=None,
        )
        for handler in self._logger.handlers:
            handler.handle(record)

    @property
    def raw(self) -> logging.Logger:
        return self._logger


    
# log = SimpleLogger(level=LogLevel.DEBUG)

# log.debug("debug details")
# log.info("normal output")
# # Example usage in characteristic sample computation
# import sys

# log = SimpleLogger(level=LogLevel.INFO, stream=sys.stderr)
# log.warn("this goes to stderr")

# log = SimpleLogger(
#     name="solver",
#     level=LogLevel.DEBUG,
#     logfile="solver.log"
# )

# log.info("starting solver")
# log.debug("state = 42")


# log = SimpleLogger(level=LogLevel.SILENT)

# log.info("not printed")
# log.error("not printed")

# self._logger.addHandler(logging.StreamHandler(sys.stdout))
# self._logger.addHandler(logging.FileHandler("app.log"))

# log = SimpleLogger(level=LogLevel.INFO)

# # log.info("x=", 10)

# log_print = LogPrinter(log.raw)

# log_print.info("hello", 42)
# log_print.info("x =", 10)
# log_print.debug("detailed debug:", [1,2,3])
# x_ = 123
# log_print.warn(f"a warning message {x_}")
# log.set_level(LogLevel.SILENT)
# log_print.force("shown anyway")

# print = log_print

# print("This goes through the logger at INFO level")



