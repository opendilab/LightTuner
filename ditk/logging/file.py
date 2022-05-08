import logging
import os
import pathlib
from typing import Optional

from .base import _LogLevelType


def _normpath(path: str) -> str:
    return os.path.normcase(os.path.normpath(os.path.abspath(path)))


class LoggingFileHandler(logging.FileHandler):
    def __init__(self, filename: str, mode: str = 'a', encoding: Optional[str] = None, delay: bool = False,
                 **kwargs) -> None:
        logging.FileHandler.__init__(self, filename, mode, encoding, delay, **kwargs)
        self.__file_path = _normpath(filename)

    @property
    def file_path(self) -> str:
        """
        Unique path of the file.
        """
        return self.__file_path


_FILE_FMT = logging.Formatter(
    fmt='[%(asctime)s][%(filename)s:%(lineno)d][%(levelname)s] %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S",
)


def _create_local_file(filename: str) -> str:
    filepath, name = os.path.split(os.path.abspath(filename))
    os.makedirs(filepath, exist_ok=True)
    pathlib.Path(filename).touch()
    return filename


def _create_file_handler(path: str, mode: str = 'a', level: _LogLevelType = logging.NOTSET) -> LoggingFileHandler:
    logger_file_path = _create_local_file(path)
    handler = LoggingFileHandler(logger_file_path, mode)
    handler.setFormatter(_FILE_FMT)
    handler.setLevel(level)
    return handler
