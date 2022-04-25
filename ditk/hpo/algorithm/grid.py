from typing import Tuple, Iterator

from hbutils.reflection import nested_for

from .base import BaseAlgorithm
from ..space import ContinuousSpace, SeparateSpace, FixedSpace
from ..utils import ValueProxyLock
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


class GridAlgorithm(BaseAlgorithm):
    def __init__(self, max_steps, **kwargs):
        BaseAlgorithm.__init__(self, max_steps, False)

    def _iter_spaces(self, vsp: Tuple[HyperValue, ...], pres: ValueProxyLock) -> Iterator[Tuple[object, ...]]:
        alloc_n, remain_n = 0, self.max_steps * 1.0
        for vitem in vsp:
            space = vitem.space
            if isinstance(space, (ContinuousSpace, SeparateSpace)):
                alloc_n += 1
            remain_n /= space.length

        dim_alloc = []
        for vitem in vsp:
            space = vitem.space
            if isinstance(space, (ContinuousSpace, SeparateSpace)):
                alloc_length = int(max(round(space.length * remain_n ** (1 / alloc_n)), 1))
                if space.count is not None:
                    alloc_length = min(alloc_length, space.count)
                if isinstance(space, ContinuousSpace):
                    dim_alloc.append(allocate_continuous(space, alloc_length))
                else:
                    dim_alloc.append(allocate_separate(space, alloc_length))

                alloc_n -= 1
                remain_n /= alloc_length / space.length
            elif isinstance(space, FixedSpace):
                dim_alloc.append(allocate_fixed(space))
            else:
                raise TypeError(f'Unknown space type - {repr(space)}.')

        final_alloc = map(lambda x: tuple(x[0].trans(vx) for vx in x[1]), zip(vsp, dim_alloc))
        for tpl in nested_for(*final_alloc):
            yield tuple(tpl)
            _ = pres.get()
