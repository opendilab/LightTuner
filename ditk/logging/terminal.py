import logging
import os
from logging import LogRecord

from .base import _LogLevelType
from .rich import _create_rich_handler
from .stream import _create_stream_handler


def _use_rich() -> bool:
    return not os.environ.get('DISABLE_RICH', '').strip()


class LoggingTerminalHandler(logging.Handler):
    """
    Overview:
        A handler customized in ``ditk``.

        When ``DISABLE_RICH`` environment variable is set to non-empty, log will be printed to \
        ordinary ``StreamHandler``, otherwise ``rich.logging.RichHandler`` will be used.
    """

    def __init__(self, use_stdout: bool = False, level: _LogLevelType = logging.NOTSET):
        """
        Constructor of :class:`TerminalHandler`.

        :param use_stdout: Use ``sys.stdout`` instead of ``sys.stderr``.
        :param level: Log level.
        """
        logging.Handler.__init__(self, level)
        self.use_stdout = not not use_stdout

    def _get_current_handler(self) -> logging.Handler:
        if _use_rich():
            return _create_rich_handler(self.use_stdout, self.level)
        else:
            return _create_stream_handler(self.use_stdout, self.level)

    def emit(self, record: LogRecord) -> None:
        """
        Emit the log record to handler.

        If ``DISABLE_RICH`` environment variable is set to non-empty, this method is equal to \
        :meth:`logging.StreamHandler.emit`, otherwise equals to :meth:`rich.logging.RichHandler.emit`.
        """
        return self._get_current_handler().emit(record)
