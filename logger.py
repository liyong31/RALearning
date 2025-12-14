from enum import IntEnum
import sys
from typing import TextIO, Optional


class LogLevel(IntEnum):
    SILENT = 0
    INFO = 1
    DEBUG = 2


class Logger:
    def __init__(
        self,
        level: LogLevel = LogLevel.INFO,
        stream: TextIO = sys.stdout,
    ):
        self.level = level
        self._stream: TextIO = stream
        self._owns_stream = False  # whether we opened the file ourselves

    # --------------------
    # Configuration
    # --------------------

    def set_level(self, level: LogLevel):
        self.level = level

    def set_stream(self, stream: TextIO):
        self._close_if_needed()
        self._stream = stream
        self._owns_stream = False

    def set_file(self, path: str, mode: str = "a"):
        self._close_if_needed()
        self._stream = open(path, mode)
        self._owns_stream = True

    def close(self):
        self._close_if_needed()

    def _close_if_needed(self):
        if self._owns_stream and self._stream:
            self._stream.close()
        self._owns_stream = False

    # --------------------
    # Logging primitives
    # --------------------

    def _log(self, prefix: str, msg: str):
        print(prefix + msg, file=self._stream, flush=True)

    def debug(self, msg: str):
        if self.level >= LogLevel.DEBUG:
            self._log("[DEBUG] ", msg)

    def info(self, msg: str):
        if self.level >= LogLevel.INFO:
            self._log("[MSG] ", msg)

    def warn(self, msg: str):
        if self.level >= LogLevel.INFO:
            self._log("[WARN] ", msg)

    def error(self, msg: str):
        if self.level >= LogLevel.INFO:
            self._log("[ERROR] ", msg)

# logger = Logger(LogLevel.SILENT)

# logger.debug("debug message")
# logger.info("normal output")
# logger.warn("warning message")
# logger.error("error message")


# logger = Logger(LogLevel.INFO)

# logger.info("console output")

# logger.set_file("run.log")
# logger.info("file output")

# logger.set_stream(sys.stdout)
# logger.info("back to console")
# logger.close()
