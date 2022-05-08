import logging
from typing import List, Optional

from .base import _LogLevelType
from .file import _create_file_handler, LoggingFileHandler, _normpath
from .rich import _is_simple_rich
from .stream import _is_simple_stream
from .terminal import _is_simple_terminal, LoggingTerminalHandler


def _is_simple_handler(handler: logging.Handler) -> bool:
    return _is_simple_stream(handler) or _is_simple_rich(handler) or _is_simple_terminal(handler)


def get_logger(name: Optional[str] = None,
               with_files: Optional[List[str]] = None,
               level: Optional[_LogLevelType] = None,
               use_stdout: Optional[bool] = None) -> logging.Logger:
    """
    Overview:
        Get :class:`logging.Logger` object, with terminal output and file output.

    :param name: Name of logger.
    :param with_files: The files going to output.
    :param level: Log level (just logger, handlers will be set to ``logging.NOTSET``).
    :param use_stdout: Use ``sys.stdout`` instead of ``sys.stderr``, default is ``False``.
    :return logger: Logger created.
    """
    with_files = with_files or []

    logger = logging.getLogger(name)
    if level is not None:
        logger.setLevel(level)
    to_be_logged = []

    has_simple_handler = False
    terminal_handler: Optional[LoggingTerminalHandler] = None
    file_handlers: List[LoggingFileHandler] = []
    for handler in logger.handlers:
        if _is_simple_handler(handler):
            has_simple_handler = True
        if isinstance(handler, LoggingFileHandler):
            file_handlers.append(handler)
        if isinstance(handler, LoggingTerminalHandler):
            terminal_handler = handler

    if not has_simple_handler:
        terminal_handler = LoggingTerminalHandler(bool(use_stdout))
        logger.addHandler(terminal_handler)
    else:
        to_be_logged.append(
            (logging.WARNING, "Because a terminal handler is detected in the global configuration, "
                              "no more terminal handlers will be added, and the original will be preserved "
                              "to avoid any conflicts.")
        )
        if terminal_handler and use_stdout is not None \
                and bool(use_stdout) != bool(terminal_handler.use_stdout):
            to_be_logged.append(
                (logging.WARNING, f"The original terminal handler is using "
                                  f"sys.{'stdout' if terminal_handler.use_stdout else 'stderr'}, "
                                  f"but this will be changed to sys.{'stdout' if use_stdout else 'stderr'} "
                                  f"due to the setting of 'use_stdout': {repr(use_stdout)}.")
            )
            terminal_handler.use_stdout = use_stdout

    fps = {handler.file_path for handler in file_handlers}
    for file in (with_files or []):
        if _normpath(file) in fps:
            to_be_logged.append(
                (logging.WARNING, f"File {repr(file)} has already been added to this logger, "
                                  f"so this configuration will be ignored.")
            )
        else:
            handler = _create_file_handler(file)
            logger.addHandler(handler)
            fps.add(_normpath(file))

    for level_, msg in to_be_logged:
        logger.log(level_, msg)

    return logger
