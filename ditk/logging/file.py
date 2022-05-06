import logging
import os

from .base import _to_fmt

_FILE_FMT = logging.Formatter(
    fmt='[%(asctime)s][%(filename)15s][line:%(lineno)4d][%(levelname)8s] %(message)s',
)


def _create_local_file(filename: str) -> str:
    filepath, name = os.path.split(os.path.abspath(filename))
    os.makedirs(filepath, exist_ok=True)
    with open(filename, 'a'):
        pass

    return filename


def _create_file_handler(path: str, mode: str = 'a', fmt: logging.Formatter = None) -> logging.FileHandler:
    logger_file_path = _create_local_file(path)
    handler = logging.FileHandler(logger_file_path, mode)
    handler.setFormatter(_to_fmt(fmt or _FILE_FMT))
    return handler
