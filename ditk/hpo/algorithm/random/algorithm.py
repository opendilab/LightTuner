from typing import Optional, Any, Tuple

from .allocation import make_native_random, random_space_value
from ..base import BaseConfigure, BaseAlgorithm, BaseSession, Task
from ...space import BaseSpace, ContinuousSpace
from ...utils import ThreadService, ServiceNoLongerAccept
from ...value import HyperValue


class RandomConfigure(BaseConfigure):
    def seed(self, s: Optional[int] = None):
        self._settings['seed'] = s
        return self


class RandomAlgorithm(BaseAlgorithm):
    def __init__(self, seed=None, max_steps=None, **kwargs):
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

        self._max_count = 1
        for hv in self.vsp:
            space: BaseSpace = hv.space
            if isinstance(space, ContinuousSpace):
                self._max_count = None
                break
            else:
                self._max_count *= space.count

    def _random_hyper_value(self, hv: HyperValue):
        return hv.trans(random_space_value(hv.space, self.__algorithm.random))

    def _create_new_value(self) -> Tuple[Any, ...]:
        return tuple(self._random_hyper_value(hv) for hv in self.vsp)

    def _return_on_success(self, task: Task, retval: Any):
        pass

    def _run(self):
        _step_id, _max_step = 0, self.__algorithm.max_steps
        while _max_step is None or _step_id < _max_step:
            _step_id += 1
            try:
                self._put_via_space(self._create_new_value())
            except ServiceNoLongerAccept:  # service is down
                break
            except NoMoreRandomSample:  # all the sample has been iterated
                break
