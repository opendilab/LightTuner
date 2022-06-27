import math
from typing import Tuple, Dict, Type, List, Union, Any

from hbutils.reflection import nested_for

from .base import BaseAlgorithm, BaseConfigure, BaseSession
from ..space import ContinuousSpace, SeparateSpace, FixedSpace, BaseSpace
from ..utils import ThreadService
from ..value import HyperValue


def allocate_continuous(space: ContinuousSpace, n: int) -> Tuple[float, ...]:
    if n == 1:
        return ((space.lbound + space.ubound) / 2,)
    else:
        return tuple(map(lambda x: (x / (n - 1)) * (space.ubound - space.lbound) + space.lbound, range(n)))


def allocate_separate(space: SeparateSpace, cnt: int) -> Tuple[float, ...]:
    def _postprocess(i_):
        return i_ * space.step + space.start

    if cnt == 1:
        return (_postprocess((space.count - 1) // 2),)
    elif cnt > space.count:
        return allocate_separate(space, space.count)
    else:
        unit = (space.count - 1) * 1.0 / (cnt - 1)
        return tuple(map(lambda x: _postprocess(round(x * unit)), range(cnt)))


def allocate_fixed(space: FixedSpace) -> Tuple[int, ...]:
    return tuple(range(space.count))


_ORDER_DICT: Dict[Type[BaseSpace], int] = {
    FixedSpace: 1,
    SeparateSpace: 2,
    ContinuousSpace: 3,
}


class GridConfigure(BaseConfigure):
    pass


class GridAlgorithm(BaseAlgorithm):
    def __init__(self, max_steps, **kwargs):
        self.max_steps = max_steps

    def get_session(self, space, service: ThreadService) -> 'GridSession':
        return GridSession(self, space, service)


class GridSession(BaseSession):
    def __init__(self, algorithm: GridAlgorithm, space, service: ThreadService):
        BaseSession.__init__(self, space, service)
        self.__algorithm = algorithm

    def _return_on_success(self, task: Tuple[int, Any, Any], retval: Any):
        # just do nothing at all
        # _task_id, _config, _attachment = task
        print(task, retval.value)
        pass

    def _run(self, vsp: Tuple[HyperValue, ...]):
        _alloc_count = self.__algorithm.max_steps
        if _alloc_count is None:
            _alloc_count = +math.inf

        ordered = sorted([(
            (
                _ORDER_DICT[type(sp.space)],
                sp.space.count if isinstance(sp.space, SeparateSpace) else 0,
            ), i, sp
        ) for i, sp in enumerate(vsp)])
        ovsp: Tuple[HyperValue, ...] = tuple(sp for _, _, sp in ordered)
        oord: Tuple[int, ...] = tuple(i for _, i, _ in ordered)

        if math.isinf(_alloc_count) and ovsp and isinstance(ovsp[-1].space, ContinuousSpace):
            raise ValueError('Continuous space is not supported when max step is not assigned.')

        alloc_n, remain_n = 0, _alloc_count * 1.0
        for vitem in ovsp:
            space = vitem.space
            if isinstance(space, (ContinuousSpace, SeparateSpace)):
                alloc_n += 1
            remain_n /= space.length

        dim_alloc: List[Tuple[Union[int, float], ...]] = []
        for vitem in ovsp:
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

        odim_alloc = [None] * len(vsp)
        for oi, da in zip(oord, dim_alloc):
            odim_alloc[oi] = da

        final_alloc = map(lambda x: tuple(x[0].trans(vx) for vx in x[1]), zip(vsp, odim_alloc))
        for tpl in nested_for(*final_alloc):
            self._put_via_space(tuple(tpl))
