import io
import os
from typing import Iterable, Tuple, Any


def sblock(s: str) -> str:
    n = len(s.splitlines())
    nl = len(str(n))
    with io.StringIO() as sf:
        for lineno, line in enumerate(s.splitlines(), start=1):
            sf.write(" " * (nl - len(str(lineno))) + str(lineno) + u' \u2502 ' + line + os.linesep)

        return sf.getvalue()


def rchain(reprs: Iterable[Tuple[str, Any]]) -> str:
    return f"{', '.join(name + ': ' + repr(obj) for name, obj in reprs)}"
