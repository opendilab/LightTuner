import logging
import os

from .base import _LogLevelType

_FILE_FMT = logging.Formatter(
    fmt='[%(asctime)s][%(filename)s:%(lineno)d][%(levelname)s] %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S",
)


def _create_local_file(filename: str) -> str:
    filepath, name = os.path.split(os.path.abspath(filename))
    os.makedirs(filepath, exist_ok=True)
    with open(filename, 'a'):
        pass

    return filename


def _create_file_handler(path: str, mode: str = 'a', level: _LogLevelType = logging.NOTSET) -> logging.FileHandler:
    logger_file_path = _create_local_file(path)
    handler = logging.FileHandler(logger_file_path, mode)
    handler.setFormatter(_FILE_FMT)
    handler.setLevel(level)
    return handler
