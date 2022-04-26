from enum import IntEnum, unique
from typing import Iterator, Tuple

from hbutils.model import int_enum_loads

from ..utils import ValueProxyLock
from ..value import HyperValue, struct_values


@int_enum_loads(name_preprocess=str.upper)
@unique
class OptimizeDirection(IntEnum):
    MAXIMIZE = 1
    MINIMIZE = 2


class BaseAlgorithm:
    def __init__(self, **kwargs):
        pass

    def _iter_spaces(self, vsp: Tuple[HyperValue, ...], pres: ValueProxyLock) -> Iterator[Tuple[object, ...]]:
        raise NotImplementedError  # pragma: no cover

    def iter_config(self, vs, pres: ValueProxyLock) -> Iterator[object]:
        sfunc, svalues = struct_values(vs)
        for vargs in self._iter_spaces(svalues, pres):
            yield sfunc(*vargs)


class BaseOptimizeAlgorithm(BaseAlgorithm):
    def __init__(self, opt_direction, **kwargs):
        BaseAlgorithm.__init__(self, **kwargs)
        if opt_direction is None:
            raise ValueError(f'Direction {opt_direction} is not allowed.')
        self.__opt_direction = OptimizeDirection.loads(opt_direction)

    @property
    def opt_direction(self) -> OptimizeDirection:
        return self.__opt_direction

    def _iter_spaces(self, vsp: Tuple[HyperValue, ...], pres: ValueProxyLock) -> Iterator[Tuple[object, ...]]:
        raise NotImplementedError  # pragma: no cover
