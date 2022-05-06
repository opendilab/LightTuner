import logging
import os
import sys
from functools import lru_cache
from typing import Union

from rich.logging import RichHandler

from .rich import _create_rich_handler
from .stream import _create_stream_handler

_USE_RICH = not os.environ.get('DISABLE_RICH', '').strip()


@lru_cache()
def _get_terminal_handler() -> Union[logging.StreamHandler, RichHandler]:
    if _USE_RICH:
        return _create_rich_handler()
    else:
        return _create_stream_handler()


def _is_ordinal_stream_handler(handler: logging.Handler) -> bool:
    return isinstance(handler, logging.StreamHandler) and (
            handler.stream is sys.stdout or
            handler.stream is sys.stderr)


def _is_ordinal_rich_handler(handler: logging.Handler) -> bool:
    return isinstance(handler, RichHandler) and (
            handler.console.file is sys.stdout or
            handler.console.file is sys.stderr)


def _is_ordinal_terminal_handler(handler: logging.Handler):
    return _is_ordinal_stream_handler(handler) or _is_ordinal_rich_handler(handler)
