import logging

__all__ = [
    'CRITICAL',
    'FATAL',
    'ERROR',
    'WARNING',
    'WARN',
    'INFO',
    'DEBUG',
    'NOTSET',
    'Logger',
    'Handler',
    "FileHandler",
    'StreamHandler',
    'NullHandler',
    'getLogger',
]

CRITICAL = logging.CRITICAL
FATAL = logging.FATAL
ERROR = logging.ERROR
WARNING = logging.WARNING
WARN = logging.WARN
INFO = logging.INFO
DEBUG = logging.DEBUG
NOTSET = logging.NOTSET

Logger = logging.Logger
Handler = logging.Handler
FileHandler = logging.FileHandler
StreamHandler = logging.StreamHandler
NullHandler = logging.NullHandler

getLogger = logging.getLogger
