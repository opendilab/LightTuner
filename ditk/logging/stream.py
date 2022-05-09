import logging
import sys
from logging import StreamHandler

from .base import _LogLevelType

_STREAM_FMT = logging.Formatter(
    fmt='[%(asctime)s][%(filename)s:%(lineno)d][%(levelname)s] %(message)s',
    datefmt="%m-%d %H:%M:%S",
)


def _create_stream_handler(use_stdout: bool = False, level: _LogLevelType = logging.NOTSET) -> StreamHandler:
    handler = StreamHandler(sys.stdout if use_stdout else sys.stderr)
    handler.setFormatter(_STREAM_FMT)
    handler.setLevel(level)
    return handler
