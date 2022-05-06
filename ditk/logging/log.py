import logging
from threading import Lock
from typing import List, Optional, Union

from .file import _create_file_handler
from .terminal import _is_ordinal_terminal_handler, _get_terminal_handler

_DEFAULT_LOGGER_NAME = logging.root.name
_LOGGER_POOL = {}
_LOGGER_LOCK = Lock()


def get_logger(name: Optional[str] = None,
               with_files: List[str] = None,
               level: Union[int, str] = None) -> logging.Logger:
    with _LOGGER_LOCK:
        name = name or _DEFAULT_LOGGER_NAME
        with_files = with_files or []

        global _LOGGER_POOL
        if name in _LOGGER_POOL:
            logger = _LOGGER_POOL[name]
            if with_files or level is not None:
                logger.warn(f'Logger {repr(name)} has already exist, extra arguments '
                            f'(with_files: {repr(with_files)}, level: {repr(level)}) will be ignored.')
            return logger

        logger = logging.getLogger(name)
        if level is not None:
            logger.setLevel(level)

        has_terminal_handler = False
        for handler in logger.handlers:
            if _is_ordinal_terminal_handler(handler):
                has_terminal_handler = True
                break

        if not has_terminal_handler:
            handler = _get_terminal_handler()
            if level is not None:
                handler.setLevel(level)
            logger.addHandler(handler)

        for file in (with_files or []):
            handler = _create_file_handler(file)
            if level is not None:
                handler.setLevel(level)
            logger.addHandler(handler)

        _LOGGER_POOL[name] = logger
        return logger
