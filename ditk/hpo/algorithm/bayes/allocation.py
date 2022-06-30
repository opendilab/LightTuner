import math
from typing import Callable, Tuple

from ...space import ContinuousSpace, SeparateSpace, FixedSpace
from ...value import HyperValue


def hyper_to_bound(hv: HyperValue) -> Tuple[Tuple[float, float], Callable]:
    space = hv.space
    if isinstance(space, ContinuousSpace):
        return (space.lbound, space.ubound), hv.trans
    elif isinstance(space, SeparateSpace):
        n = space.count
        _start, _step = space.start, space.step

        def _trans(x):
            rx = int(min(math.floor(x), n - 1))
            ax = _start + rx * _step
            return hv.trans(ax)

        return (0.0, float(n)), _trans
    elif isinstance(space, FixedSpace):
        raise TypeError(f'Fixed space is not supported in bayesian optimization, but {hv!r} found.')
    else:
        raise TypeError(f'Unknown space type - {space!r}.')  # pragma: no cover
