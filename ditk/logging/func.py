import logging
from functools import lru_cache

from .base import _LogLevelType
from .log import get_logger

__all__ = [
    'CRITICAL', 'FATAL', 'ERROR',
    'WARNING', 'WARN', 'INFO', 'DEBUG', 'NOTSET',
    'critical', 'fatal', 'error', 'exception',
    'warning', 'warn', 'info', 'debug', 'log',
    'set_level',
]

CRITICAL = logging.CRITICAL
FATAL = logging.FATAL
ERROR = logging.ERROR
WARNING = logging.WARNING
WARN = logging.WARN
INFO = logging.INFO
DEBUG = logging.DEBUG
NOTSET = logging.NOTSET


@lru_cache()
def _root():
    return get_logger()


def critical(msg, *args, **kwargs):
    """
    Log a message with severity 'CRITICAL' on the root logger. If the logger
    has no handlers, call basicConfig() to add a console handler with a
    pre-defined format.
    """
    _root().critical(msg, *args, **kwargs)


fatal = critical


def error(msg, *args, **kwargs):
    """
    Log a message with severity 'ERROR' on the root logger. If the logger has
    no handlers, call basicConfig() to add a console handler with a pre-defined
    format.
    """
    _root().error(msg, *args, **kwargs)


def exception(msg, *args, exc_info=True, **kwargs):
    """
    Log a message with severity 'ERROR' on the root logger, with exception
    information. If the logger has no handlers, basicConfig() is called to add
    a console handler with a pre-defined format.
    """
    error(msg, *args, exc_info=exc_info, **kwargs)


def warning(msg, *args, **kwargs):
    """
    Log a message with severity 'WARNING' on the root logger. If the logger has
    no handlers, call basicConfig() to add a console handler with a pre-defined
    format.
    """
    _root().warning(msg, *args, **kwargs)


def warn(msg, *args, **kwargs):
    warning(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    """
    Log a message with severity 'INFO' on the root logger. If the logger has
    no handlers, call basicConfig() to add a console handler with a pre-defined
    format.
    """
    _root().info(msg, *args, **kwargs)


def debug(msg, *args, **kwargs):
    """
    Log a message with severity 'DEBUG' on the root logger. If the logger has
    no handlers, call basicConfig() to add a console handler with a pre-defined
    format.
    """
    _root().debug(msg, *args, **kwargs)


def log(level, msg, *args, **kwargs):
    """
    Log 'msg % args' with the integer severity 'level' on the root logger. If
    the logger has no handlers, call basicConfig() to add a console handler
    with a pre-defined format.
    """
    _root().log(level, msg, *args, **kwargs)


def set_level(level: _LogLevelType):
    """
    Overview:
        Set level of the root log.
    """
    _root().setLevel(level)
