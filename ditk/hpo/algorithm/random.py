import random
from typing import Iterator

from ..space import SeparateSpace, ContinuousSpace, FixedSpace, BaseSpace
from ..value import HyperValue, struct_values


class RandomAlgorithm:
    def __init__(self, steps):
        self.__steps = steps

    @classmethod
    def _random_space_value(cls, space: BaseSpace):
        if isinstance(space, SeparateSpace):
            return random.randint(0, space.count - 1) * space.step + space.start
        elif isinstance(space, ContinuousSpace):
            return random.random() * (space.rbound - space.lbound) + space.lbound
        elif isinstance(space, FixedSpace):
            return random.randint(0, space.count - 1)
        else:
            raise TypeError(f'Unknown space type - {repr(space)}.')

    @classmethod
    def _random_hyper_value(cls, hv: HyperValue):
        space = hv.space
        return hv.trans(cls._random_space_value(space))

    def iter_config(self, vs) -> Iterator[object]:
        sfunc, svalues = struct_values(vs)
        for i in range(self.__steps):
            yield sfunc(*map(self._random_hyper_value, svalues))
