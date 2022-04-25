from typing import Iterator, Optional, Tuple

from ..utils import ValueProxyLock
from ..value import HyperValue, struct_values


class BaseAlgorithm:
    def __init__(self, max_steps: Optional[int], allow_unlimited_steps: bool = False):
        if not allow_unlimited_steps and max_steps is None:
            raise ValueError(f'Unlimited steps is not allowed in {repr(self.__class__)}.')
        self.__max_steps = max_steps

    @property
    def max_steps(self) -> Optional[int]:
        return self.__max_steps

    def _iter_spaces(self, vsp: Tuple[HyperValue, ...], pres: ValueProxyLock) -> Iterator[Tuple[object, ...]]:
        raise NotImplementedError  # pragma: no cover

    def iter_config(self, vs, pres: ValueProxyLock) -> Iterator[object]:
        sfunc, svalues = struct_values(vs)
        for vargs in self._iter_spaces(svalues, pres):
            yield sfunc(*vargs)
