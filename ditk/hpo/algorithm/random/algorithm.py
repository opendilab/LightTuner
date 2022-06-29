from functools import reduce
from operator import __mul__
from typing import Optional, Any, Tuple, Set

from hbutils.string import plural_word

from .allocation import make_native_random, random_space_value
from ..base import BaseConfigure, BaseAlgorithm, BaseSession, Task
from ...space import ContinuousSpace
from ...utils import ThreadService, ServiceNoLongerAccept
from ...value import HyperValue


class RandomConfigure(BaseConfigure):
    def seed(self, s: Optional[int] = None):
        self._settings['seed'] = s
        return self


class RandomAlgorithm(BaseAlgorithm):
    def __init__(self, seed=None, max_steps=None, **kwargs):
        BaseAlgorithm.__init__(self, seed=seed, max_steps=max_steps, **kwargs)
        self.random = make_native_random(seed)
        self.max_steps = max_steps

    def get_session(self, space, service: ThreadService) -> 'RandomSession':
        return RandomSession(self, space, service)


class NoMoreRandomSample(Exception):
    pass


class RandomSession(BaseSession):
    def __init__(self, algorithm: RandomAlgorithm, space, service: ThreadService):
        BaseSession.__init__(self, space, service)
        self.__algorithm = algorithm

        self._limited_space: bool = not any(isinstance(hv.space, ContinuousSpace) for hv in self.vsp)
        if self._limited_space:
            self._total_pairs: Optional[int] = reduce(__mul__, (hv.space.count for hv in self.vsp))
            self._exist_pairs: Optional[Set] = set()
        else:
            self._total_pairs: Optional[int] = None
            self._exist_pairs: Optional[Set] = None

    def _random_hyper_value(self, hv: HyperValue):
        return hv.trans(random_space_value(hv.space, self.__algorithm.random))

    def _create_one_sample(self) -> Tuple[Any, ...]:
        return tuple(self._random_hyper_value(hv) for hv in self.vsp)

    def _create_new_sample(self) -> Tuple[Any, ...]:
        if self._limited_space:
            if len(self._exist_pairs) < self._total_pairs:
                while True:
                    _sample = self._create_one_sample()
                    if _sample not in self._exist_pairs:
                        self._exist_pairs.add(_sample)
                        return _sample
            else:
                raise NoMoreRandomSample(f'All {plural_word(self._total_pairs, "sample")} iterated, '
                                         f'no more random sample can be provided.')
        else:
            return self._create_one_sample()

    def _return_on_success(self, task: Task, retval: Any):
        pass

    def _run(self):
        _step_count, _max_step = 0, self.__algorithm.max_steps
        while _max_step is None or _step_count < _max_step:
            _step_count += 1
            try:
                _sample: Tuple[Any, ...] = self._create_new_sample()
            except NoMoreRandomSample:  # all the samples have been run out
                break

            try:
                self._put_via_space(_sample)
            except ServiceNoLongerAccept:  # service is down
                break
