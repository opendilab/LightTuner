import random
from itertools import cycle
from typing import Iterator, Tuple

from .base import BaseAlgorithm
from ..space import SeparateSpace, ContinuousSpace, FixedSpace, BaseSpace
from ..value import HyperValue


def _random_space_value(space: BaseSpace):
    if isinstance(space, SeparateSpace):
        return random.randint(0, space.count - 1) * space.step + space.start
    elif isinstance(space, ContinuousSpace):
        return random.random() * (space.rbound - space.lbound) + space.lbound
    elif isinstance(space, FixedSpace):
        return random.randint(0, space.count - 1)
    else:
        raise TypeError(f'Unknown space type - {repr(space)}.')


class RandomAlgorithm(BaseAlgorithm):
    def __init__(self, max_steps):
        BaseAlgorithm.__init__(self, max_steps, allow_unlimited_steps=True)

    @classmethod
    def _random_hyper_value(cls, hv: HyperValue):
        return hv.trans(_random_space_value(hv.space))

    def _iter_spaces(self, vsp: Tuple[HyperValue, ...]) -> Iterator[Tuple[object, ...]]:
        iter_obj = cycle([0]) if self.max_steps is None else range(self.max_steps)
        for _ in iter_obj:
            yield tuple(map(self._random_hyper_value, vsp))
