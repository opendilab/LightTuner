import logging
import os
from logging import LogRecord
from typing import Optional

from .base import _LogLevelType
from .rich import _create_rich_handler, _is_simple_rich
from .stream import _create_stream_handler, _is_simple_stream


def _use_rich() -> bool:
    return not os.environ.get('DISABLE_RICH', '').strip()


class LoggingTerminalHandler(logging.Handler):
    """
    Overview:
        A handler customized in ``ditk``.

        When ``DISABLE_RICH`` environment variable is set to non-empty, log will be printed to \
        ordinary ``StreamHandler``, otherwise ``rich.logging.RichHandler`` will be used.
    """

    def __init__(self, use_stdout: bool = False, level: _LogLevelType = logging.NOTSET,
                 logger: Optional[logging.Logger] = None):
        """
        Constructor of :class:`TerminalHandler`.

        :param use_stdout: Use ``sys.stdout`` instead of ``sys.stderr``.
        :param level: Log level.
        :param logger: Logger of this handler.
        """
        logging.Handler.__init__(self, level)
        self.use_stdout = not not use_stdout
        self.logger = logger

    def _get_current_handler(self) -> logging.Handler:
        _current_logger, last_simple_handler = self.logger, None
        while _current_logger:
            for hdl in _current_logger.handlers:
                if _is_simple_handler(hdl):
                    last_simple_handler = hdl
                    break

            _current_logger = _current_logger.parent if _current_logger.propagate else None

        if not last_simple_handler or last_simple_handler is self:
            if _use_rich():
                return _create_rich_handler(self.use_stdout, self.level)
            else:
                return _create_stream_handler(self.use_stdout, self.level)
        else:
            return logging.NullHandler(self.level)

    def emit(self, record: LogRecord) -> None:
        """
        Emit the log record to handler.

        If ``DISABLE_RICH`` environment variable is set to non-empty, this method is equal to \
        :meth:`logging.StreamHandler.emit`, otherwise equals to :meth:`rich.logging.RichHandler.emit`.
        """
        return self._get_current_handler().emit(record)


def _is_simple_terminal(handler: logging.Handler) -> bool:
    return isinstance(handler, LoggingTerminalHandler)


def _is_simple_handler(handler: logging.Handler) -> bool:
    return _is_simple_stream(handler) or _is_simple_rich(handler) or _is_simple_terminal(handler)
