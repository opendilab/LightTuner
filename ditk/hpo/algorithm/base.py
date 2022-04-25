from enum import IntEnum, unique
from typing import Iterator, Optional, Tuple

from hbutils.model import int_enum_loads

from ..utils import ValueProxyLock
from ..value import HyperValue, struct_values


@int_enum_loads(name_preprocess=str.upper)
@unique
class OptimizeDirection(IntEnum):
    NOTHING = 0
    MAXIMIZE = 1
    MINIMIZE = 2


class BaseAlgorithm:
    def __init__(self, max_steps: Optional[int] = None, allow_unlimited_steps: bool = True,
                 opt_direction=OptimizeDirection.NOTHING, allow_nothing_direction: bool = True):
        self.__max_steps = max_steps
        if not allow_unlimited_steps and self.__max_steps is None:
            raise ValueError(f'Unlimited steps is not allowed in {repr(self.__class__)}.')

        self.__opt_direction = OptimizeDirection.loads(opt_direction)
        if not allow_nothing_direction and self.__opt_direction == OptimizeDirection.NOTHING:
            raise ValueError(f'Direction {self.__opt_direction} is not allowed.')

    @property
    def max_steps(self) -> Optional[int]:
        return self.__max_steps

    @property
    def opt_direction(self) -> OptimizeDirection:
        return self.__opt_direction

    def _iter_spaces(self, vsp: Tuple[HyperValue, ...], pres: ValueProxyLock) -> Iterator[Tuple[object, ...]]:
        raise NotImplementedError  # pragma: no cover

    def iter_config(self, vs, pres: ValueProxyLock) -> Iterator[object]:
        sfunc, svalues = struct_values(vs)
        for vargs in self._iter_spaces(svalues, pres):
            yield sfunc(*vargs)
