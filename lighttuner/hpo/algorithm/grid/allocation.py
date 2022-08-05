from typing import Tuple

from ...space import ContinuousSpace, SeparateSpace, FixedSpace


def allocate_continuous(space: ContinuousSpace, n: int) -> Tuple[float, ...]:
    if n == 1:
        return ((space.lbound + space.ubound) / 2, )
    else:
        return tuple(map(lambda x: (x / (n - 1)) * (space.ubound - space.lbound) + space.lbound, range(n)))


def allocate_separate(space: SeparateSpace, cnt: int) -> Tuple[float, ...]:

    def _postprocess(i_):
        return i_ * space.step + space.start

    if cnt == 1:
        return (_postprocess((space.count - 1) // 2), )
    elif cnt > space.count:
        return allocate_separate(space, space.count)
    else:
        unit = (space.count - 1) * 1.0 / (cnt - 1)
        return tuple(map(lambda x: _postprocess(round(x * unit)), range(cnt)))


def allocate_fixed(space: FixedSpace) -> Tuple[int, ...]:
    return tuple(range(space.count))
