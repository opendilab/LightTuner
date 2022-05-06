import logging
import shutil
from functools import lru_cache

from rich.console import Console
from rich.logging import RichHandler

import ditk
from .base import _to_fmt


@lru_cache()
def _get_terminal_width() -> int:
    width, _ = shutil.get_terminal_size()
    return width


@lru_cache()
def _get_rich_console() -> Console:
    return Console(width=_get_terminal_width())


_RICH_FMT = logging.Formatter(
    fmt="%(message)s",
    datefmt="[%m-%d %H:%M:%S]"
)


def _create_rich_handler(fmt: logging.Formatter = _RICH_FMT) -> RichHandler:
    handler = RichHandler(
        console=_get_rich_console(),
        rich_tracebacks=True, markup=True,
        tracebacks_suppress=[ditk],
    )
    handler.setFormatter(_to_fmt(fmt))
    return handler
