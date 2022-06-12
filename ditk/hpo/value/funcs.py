import math
from functools import partial

from .value import HyperValue
from ..space import ContinuousSpace, SeparateSpace, FixedSpace
from ..utils import l2normal

__all__ = [
    'uniform', 'quniform',
    'choice', 'randint', 'randn',
]


def uniform(lbound, ubound) -> HyperValue:
    if lbound < ubound:
        return HyperValue(ContinuousSpace(lbound, ubound))
    else:
        raise ValueError(f'Lower bound should be less than upper bound, but {lbound} >= {ubound} found.')


def quniform(start, end, step) -> HyperValue:
    if start <= end:
        if step > 0:
            return HyperValue(SeparateSpace(start, end, step))
        else:
            raise ValueError(f'Step value should be positive, but {step} found.')
    else:
        raise ValueError(f'Start value should be no greater tha end value, but {start} > {end} found.')


def choice(chs) -> HyperValue:
    if isinstance(chs, (list, tuple)):
        if len(chs) > 0:
            return HyperValue(FixedSpace(len(chs))) >> (lambda x: chs[x])
        else:
            raise ValueError(f'At least 1 choice should be contained, but {repr(chs)} found.')
    else:
        raise TypeError(f'List or tuple required, but {repr(chs)} found.')


def randint(start, end) -> HyperValue:
    return quniform(math.ceil(start), math.floor(end), 1.0) >> int


def randn(mu=0.0, sigma=1.0):
    return uniform(0.0, 1.0) >> partial(l2normal, mu=mu, sigma=sigma)
