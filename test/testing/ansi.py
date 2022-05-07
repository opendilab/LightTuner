import re

_ANSI_PATTERN = re.compile(r'\x1B\[\d+(;\d+){0,2}m')


def ansi_unescape(string: str) -> str:
    return _ANSI_PATTERN.sub('', string)
