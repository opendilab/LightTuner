import logging
import sys
from logging import StreamHandler, LogRecord

from rich.markup import render

from .base import _LogLevelType

_STREAM_FMT = logging.Formatter(
    fmt='[%(asctime)s][%(filename)s:%(lineno)d][%(levelname)s] %(message)s',
    datefmt="%m-%d %H:%M:%S",
)


def _strip_rich_markup(text: str) -> str:
    return render(text).plain


class NoRichStreamHandler(StreamHandler):

    def emit(self, record: LogRecord) -> None:
        if isinstance(record.msg, str):
            record.msg = _strip_rich_markup(record.msg)
        super().emit(record)


def _create_stream_handler(use_stdout: bool = False, level: _LogLevelType = logging.NOTSET) -> StreamHandler:
    handler = NoRichStreamHandler(sys.stdout if use_stdout else sys.stderr)
    handler.setFormatter(_STREAM_FMT)
    handler.setLevel(level)
    return handler
