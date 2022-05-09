import logging
from typing import List, Optional, Tuple

from .base import _LogLevelType
from .file import _create_file_handler, LoggingFileHandler, _normpath
from .terminal import LoggingTerminalHandler

__all__ = [
    'try_init_root', 'getLogger',
]


def try_init_root(level: Optional[_LogLevelType] = None) -> logging.Logger:
    root = logging.getLogger()
    if not root.handlers:
        root.addHandler(LoggingTerminalHandler())
    if level is not None:
        root.setLevel(level)
    return root


# noinspection PyPep8Naming
def getLogger(name: Optional[str] = None,
              level: Optional[_LogLevelType] = None,
              with_files: Optional[List[str]] = None) -> logging.Logger:
    """
    Overview:
        Get :class:`logging.Logger` object, with terminal output and file output.

    :param name: Name of logger.
    :param with_files: The files going to output.
    :return logger: Logger created.
    """

    logger = logging.getLogger(name)
    if level is not None:
        logger.setLevel(level)
    to_be_logged = []

    with_files = with_files or []
    if with_files:
        file_handlers: List[Tuple[LoggingFileHandler, logging.Logger]] = []
        _current_logger = logger
        while _current_logger:
            for handler in _current_logger.handlers:
                if isinstance(handler, LoggingFileHandler):
                    file_handlers.append((handler, _current_logger))

            _current_logger = _current_logger.parent if _current_logger.propagate else None

        fps = {handler.file_path: _logger for handler, _logger in file_handlers}
        for file in with_files:
            nfile = _normpath(file)
            if nfile in fps:
                to_be_logged.append(
                    (logging.WARNING, f"File {repr(file)} has already been added to logger {repr(fps[nfile])}, "
                                      f"so this configuration will be ignored.")
                )
            else:
                handler = _create_file_handler(file)
                logger.addHandler(handler)
                fps[nfile] = logger

    for level_, msg in to_be_logged:
        logger.log(level_, msg)

    return logger
