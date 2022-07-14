import math
from typing import Tuple, Dict, Type, List, Union, Any

from hbutils.reflection import nested_for

from .allocation import allocate_continuous, allocate_separate, allocate_fixed
from ..base import BaseAlgorithm, BaseConfigure, BaseSession, Task
from ...space import ContinuousSpace, SeparateSpace, FixedSpace, BaseSpace
from ...utils import ThreadService, ServiceNoLongerAccept
from ...value import HyperValue

_ORDER_DICT: Dict[Type[BaseSpace], int] = {
    FixedSpace: 1,
    SeparateSpace: 2,
    ContinuousSpace: 3,
}


class GridConfigure(BaseConfigure):
    pass


class GridAlgorithm(BaseAlgorithm):

    def __init__(self, max_steps, **kwargs):
        BaseAlgorithm.__init__(self, max_steps=max_steps, **kwargs)
        self.max_steps = max_steps

    def get_session(self, space, service: ThreadService) -> 'GridSession':
        return GridSession(self, space, service)


class GridSession(BaseSession):

    def __init__(self, algorithm: GridAlgorithm, space, service: ThreadService):
        BaseSession.__init__(self, space, service)
        self.__algorithm = algorithm

        self._alloc_count = self.__algorithm.max_steps
        if self._alloc_count is None:
            self._alloc_count = +math.inf

        ordered = sorted(
            [
                ((
                    _ORDER_DICT[type(sp.space)],
                    sp.space.count if isinstance(sp.space, SeparateSpace) else 0,
                ), i, sp) for i, sp in enumerate(self.vsp)
            ]
        )
        self._ordered_vsp: Tuple[HyperValue, ...] = tuple(sp for _, _, sp in ordered)
        self._order_map: Tuple[int, ...] = tuple(i for _, i, _ in ordered)
        if math.isinf(self._alloc_count) and self._ordered_vsp \
                and isinstance(self._ordered_vsp[-1].space, ContinuousSpace):
            raise ValueError('Continuous space is not supported when max step is not assigned.')

    def _return_on_success(self, task: Task, retval: Any):
        # just do nothing at all
        # _task_id, _config, _attachment = task
        pass

    def _run(self):
        alloc_n, remain_n = 0, self._alloc_count * 1.0
        for vitem in self._ordered_vsp:
            space = vitem.space
            if isinstance(space, (ContinuousSpace, SeparateSpace)):
                alloc_n += 1
            remain_n /= space.length

        dim_alloc: List[Tuple[Union[int, float], ...]] = []
        for vitem in self._ordered_vsp:
            space = vitem.space
            if isinstance(space, (ContinuousSpace, SeparateSpace)):
                alloc_length = max(space.length * remain_n ** (1 / alloc_n), 1)
                if space.count is not None:
                    alloc_length = min(alloc_length, space.count)
                alloc_length = int(round(alloc_length))

                if isinstance(space, ContinuousSpace):
                    dim_alloc.append(allocate_continuous(space, alloc_length))
                else:
                    dim_alloc.append(allocate_separate(space, alloc_length))

                alloc_n -= 1
                remain_n /= alloc_length / space.length
            elif isinstance(space, FixedSpace):
                dim_alloc.append(allocate_fixed(space))
            else:
                raise TypeError(f'Unknown space type - {repr(space)}.')  # pragma: no cover

        odim_alloc = [v for _, v in sorted(zip(self._order_map, dim_alloc))]  # reorder the values
        final_alloc = [tuple(hv.trans(item) for item in v) for hv, v in zip(self.vsp, odim_alloc)]
        for tpl in nested_for(*final_alloc):
            try:
                self._put_via_space(tuple(tpl))
            except ServiceNoLongerAccept:  # server is down
                break
