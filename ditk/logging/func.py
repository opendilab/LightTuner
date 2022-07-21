from typing import Mapping, Any

from hbutils.testing import vpython

from .log import try_init_root as _root

__all__ = [
    'critical',
    'fatal',
    'error',
    'exception',
    'warning',
    'warn',
    'info',
    'debug',
    'log',
]

_has_stacklevel = vpython >= '3.8'


def _inc_stacklevel(kwargs: Mapping):
    """
    Increase the value of argument ``stacklevel``.
    The default value should be 1, it will be increased by 1 after this function is called.
    """
    if _has_stacklevel:
        retval = dict(kwargs)
        retval.setdefault('stacklevel', 1)
        retval['stacklevel'] += 1
        return retval
    else:
        return kwargs


def _pkwargs(kwargs: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Everytime the log functions (such as :func:`debug`, :func:`info`) is wrapped, \
    this function should be used before passing the ``kwargs`` argument to the next level.
    """
    return _inc_stacklevel(kwargs)


def critical(msg, *args, **kwargs):
    """
    Log a message with severity 'CRITICAL' on the root logger. If the logger
    has no handlers, call basicConfig() to add a console handler with a
    pre-defined format.
    """
    _root().critical(msg, *args, **_pkwargs(kwargs))


fatal = critical


def error(msg, *args, **kwargs):
    """
    Log a message with severity 'ERROR' on the root logger. If the logger has
    no handlers, call basicConfig() to add a console handler with a pre-defined
    format.
    """
    _root().error(msg, *args, **_pkwargs(kwargs))


def exception(msg, *args, exc_info=True, **kwargs):
    """
    Log a message with severity 'ERROR' on the root logger, with exception
    information. If the logger has no handlers, basicConfig() is called to add
    a console handler with a pre-defined format.
    """
    error(msg, *args, exc_info=exc_info, **_pkwargs(kwargs))


def warning(msg, *args, **kwargs):
    """
    Log a message with severity 'WARNING' on the root logger. If the logger has
    no handlers, call basicConfig() to add a console handler with a pre-defined
    format.
    """
    _root().warning(msg, *args, **_pkwargs(kwargs))


def warn(msg, *args, **kwargs):
    warning(msg, *args, **_pkwargs(kwargs))


def info(msg, *args, **kwargs):
    """
    Log a message with severity 'INFO' on the root logger. If the logger has
    no handlers, call basicConfig() to add a console handler with a pre-defined
    format.
    """
    _root().info(msg, *args, **_pkwargs(kwargs))


def debug(msg, *args, **kwargs):
    """
    Log a message with severity 'DEBUG' on the root logger. If the logger has
    no handlers, call basicConfig() to add a console handler with a pre-defined
    format.
    """
    _root().debug(msg, *args, **_pkwargs(kwargs))


def log(level, msg, *args, **kwargs):
    """
    Log 'msg % args' with the integer severity 'level' on the root logger. If
    the logger has no handlers, call basicConfig() to add a console handler
    with a pre-defined format.
    """
    _root().log(level, msg, *args, **_pkwargs(kwargs))
