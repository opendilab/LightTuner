import logging
import os
from logging import LogRecord

from .base import _LogLevelType
from .rich import _create_rich_handler
from .stream import _create_stream_handler


def _use_rich() -> bool:
    return not os.environ.get('DISABLE_RICH', '').strip()


class TerminalHandler(logging.Handler):
    """
    Overview:
        A handler customized in ``ditk``.

        When ``DISABLE_RICH`` environment variable is set to non-empty, log will be printed to \
        ordinary ``StreamHandler``, otherwise ``rich.logging.RichHandler`` will be used.
    """

    def __init__(self, use_stdout: bool = False, level: _LogLevelType = logging.NOTSET):
        logging.Handler.__init__(self, level)
        self.use_stdout = not not use_stdout

    def emit(self, record: LogRecord) -> None:
        handler = (_create_rich_handler if _use_rich() else _create_stream_handler)(self.use_stdout, self.level)
        return handler.emit(record)


def _is_simple_terminal(handler: logging.Handler) -> bool:
    return isinstance(handler, TerminalHandler)
