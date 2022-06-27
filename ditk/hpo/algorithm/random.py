import random
from random import _inst as _RANDOM_INST
from typing import Optional, Tuple, Any

from .base import BaseConfigure, BaseAlgorithm, BaseSession
from ..space import BaseSpace, SeparateSpace, ContinuousSpace, FixedSpace
from ..utils import ThreadService, ServiceNoLongerAccept
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


class RandomConfigure(BaseConfigure):
    def seed(self, s: Optional[int] = None):
        self._settings['seed'] = s
        return self


class RandomAlgorithm(BaseAlgorithm):
    def __init__(self, seed=None, max_steps=None, **kwargs):
        self.random = _make_random(seed)
        self.max_steps = max_steps

    def get_session(self, space, service: ThreadService) -> 'RandomSession':
        return RandomSession(self, space, service)


class RandomSession(BaseSession):
    def __init__(self, algorithm: RandomAlgorithm, space, service: ThreadService):
        BaseSession.__init__(self, space, service)
        self.__algorithm = algorithm

    def _random_hyper_value(self, hv: HyperValue):
        return hv.trans(random_space_value(hv.space, self.__algorithm.random))

    def _return_on_success(self, task: Tuple[int, Any, Any], retval: Any):
        pass

    def _run(self, vsp: Tuple[HyperValue, ...]):
        _step_id, _max_step = 0, self.__algorithm.max_steps
        while _max_step is None or _step_id < _max_step:
            _step_id += 1
            try:
                self._put_via_space(tuple(map(self._random_hyper_value, vsp)))
            except ServiceNoLongerAccept:
                break
