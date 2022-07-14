import logging
import shutil
from functools import lru_cache

from rich.console import Console
from rich.logging import RichHandler

import ditk
from .base import _LogLevelType

# This value is set due the requirement of displaying the tables
_DEFAULT_WIDTH = 170


@lru_cache()
def _get_terminal_width() -> int:
    width, _ = shutil.get_terminal_size(fallback=(_DEFAULT_WIDTH, 24))
    return width


@lru_cache()
def _get_rich_console(use_stdout: bool = False) -> Console:
    return Console(width=_get_terminal_width(), stderr=not use_stdout)


_RICH_FMT = logging.Formatter(fmt="%(message)s", datefmt="[%m-%d %H:%M:%S]")


def _create_rich_handler(use_stdout: bool = False, level: _LogLevelType = logging.NOTSET) -> RichHandler:
    handler = RichHandler(
        level=level,
        console=_get_rich_console(use_stdout),
        rich_tracebacks=True,
        markup=True,
        tracebacks_suppress=[ditk],
    )
    handler.setFormatter(_RICH_FMT)
    return handler
