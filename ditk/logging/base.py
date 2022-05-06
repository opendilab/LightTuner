import logging
from typing import Union

_LogLevelType = Union[int, str]


def _to_fmt(fmt: Union[str, logging.Formatter]) -> logging.Formatter:
    if isinstance(fmt, str):
        return logging.Formatter(fmt)
    elif isinstance(fmt, logging.Formatter):
        return fmt
    else:
        raise TypeError(f'Unknown format type - {repr(fmt)}.')
