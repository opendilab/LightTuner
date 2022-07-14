import logging
from contextlib import contextmanager
from functools import wraps
from typing import ContextManager


@contextmanager
def with_root_logger(handlers=None) -> ContextManager[logging.Logger]:
    root = logging.getLogger()
    name, level, parent = root.name, root.level, root.parent
    propagate, disabled, handlers_ = root.propagate, root.disabled, list(root.handlers)

    try:
        if handlers is not None:
            root.handlers = handlers

        yield root
    finally:
        root.name = name
        root.level = level
        root.parent = parent
        root.propagate = propagate
        root.disabled = disabled
        root.handlers = handlers_


def init_handlers(handlers=None):

    def _decorator(func):

        @wraps(func)
        def _new_func(*args, **kwargs):
            with with_root_logger(handlers):
                return func(*args, **kwargs)

        return _new_func

    return _decorator


def no_handlers():
    return init_handlers([logging.NullHandler()])
