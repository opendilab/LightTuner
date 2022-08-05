from typing import Iterable, Tuple, Any


def rchain(reprs: Iterable[Tuple[str, Any]]) -> str:
    return f"{', '.join(name + ': ' + repr(obj) for name, obj in reprs)}"
