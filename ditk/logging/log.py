import logging
from threading import Lock
from typing import List, Optional, Dict

from .base import _LogLevelType
from .file import _create_file_handler
from .rich import _is_simple_rich
from .stream import _is_simple_stream
from .terminal import _is_simple_terminal, TerminalHandler


def _is_simple_handler(handler: logging.Handler) -> bool:
    return _is_simple_stream(handler) or _is_simple_rich(handler) or _is_simple_terminal(handler)


_DEFAULT_LOGGER_NAME = logging.root.name
_LOGGER_POOL: Dict[str, logging.Logger] = {}
_LOGGER_LOCK = Lock()


def get_logger(name: Optional[str] = None,
               with_files: List[str] = None,
               level: _LogLevelType = None,
               use_stdout: bool = False) -> logging.Logger:
    with _LOGGER_LOCK:
        name = name or _DEFAULT_LOGGER_NAME
        with_files = with_files or []

        global _LOGGER_POOL
        if name in _LOGGER_POOL:
            logger = _LOGGER_POOL[name]
            if with_files or level is not None:
                logger.warning(f'Logger {repr(name)} has already exist, extra arguments '
                               f'(with_files: {repr(with_files)}, level: {repr(level)}) will be ignored.')
            return logger

        level = logging.NOTSET if level is None else level
        logger = logging.getLogger(name)
        logger.setLevel(level)
        to_be_logged = []

        has_terminal_handler = False
        for handler in logger.handlers:
            if _is_simple_handler(handler):
                has_terminal_handler = True
                break

        if not has_terminal_handler:
            logger.addHandler(TerminalHandler(use_stdout, level))
        else:
            to_be_logged.append(
                (logging.WARNING, 'Because a terminal handler is detected in the global configuration, '
                                  'no more terminal handlers will be added, and the original will be preserved '
                                  'to avoid any conflicts.')
            )

        for file in (with_files or []):
            logger.addHandler(_create_file_handler(file, level=level))

        for level_, msg in to_be_logged:
            logger.log(level_, msg)

        _LOGGER_POOL[name] = logger
        return logger
