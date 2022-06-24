import random
from random import _inst as _RANDOM_INST
from typing import Iterator, Tuple, Optional

from .base import BaseAlgorithm, AlgorithmConfigure
from ..space import SeparateSpace, ContinuousSpace, FixedSpace, BaseSpace
from ..utils import ValueProxyLock, RunFailed
from ..value import HyperValue


def random_space_value(space: BaseSpace, rnd: random.Random):
    if isinstance(space, SeparateSpace):
        return rnd.randint(0, space.count - 1) * space.step + space.start
    elif isinstance(space, ContinuousSpace):
        return rnd.random() * (space.ubound - space.lbound) + space.lbound
    elif isinstance(space, FixedSpace):
        return rnd.randint(0, space.count - 1)
    else:
        raise TypeError(f'Unknown space type - {repr(space)}.')  # pragma: no cover


def _make_random(seed) -> random.Random:
    if isinstance(seed, random.Random):
        return seed
    elif isinstance(seed, int):
        return random.Random(seed)
    elif seed is None:
        return _RANDOM_INST
    else:
        raise TypeError(f"Unknown type of random seed - {seed!r}.")  # pragma: no cover


class RandomConfigure(AlgorithmConfigure):
    def seed(self, s: Optional[int] = None):
        self._settings['seed'] = s
        return self


class RandomSearchAlgorithm(BaseAlgorithm):
    # noinspection PyUnusedLocal
    def __init__(self, seed=None, **kwargs):
        BaseAlgorithm.__init__(self, **kwargs)
        self._random = _make_random(seed)

    def _random_hyper_value(self, hv: HyperValue):
        return hv.trans(random_space_value(hv.space, self._random))

    def _iter_spaces(self, vsp: Tuple[HyperValue, ...], pres: ValueProxyLock) -> Iterator[Tuple[object, ...]]:
        while True:
            yield tuple(map(self._random_hyper_value, vsp))
            try:
                _ = pres.get()
            except RunFailed:
                pass
