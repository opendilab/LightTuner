import logging
import sys
from logging import StreamHandler

from .base import _to_fmt

_STREAM_FMT = logging.Formatter(
    fmt=logging.BASIC_FORMAT,
)


def _create_stream_handler(use_stdout: bool = False, fmt: logging.Formatter = _STREAM_FMT):
    handler = StreamHandler(sys.stdout if use_stdout else sys.stderr)
    handler.setFormatter(_to_fmt(fmt))
    return handler
