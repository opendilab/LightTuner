import io
import os


def sblock(s: str) -> str:
    n = len(s)
    nl = len(str(n))
    with io.StringIO() as sf:
        for lineno, line in enumerate(s.splitlines(), start=1):
            sf.write(" " * (nl - len(str(lineno))) + str(lineno) + u' \u2502 ' + line + os.linesep)

        return sf.getvalue()
