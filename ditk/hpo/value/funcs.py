from .value import HyperValue
from ..space import ContinuousSpace, SeparateSpace, FixedSpace


def uniform(lbound, ubound):
    if lbound < ubound:
        return HyperValue(ContinuousSpace(lbound, ubound))
    else:
        raise ValueError(f'Lower bound should be less than upper bound, but {lbound} >= {ubound} found.')


def quniform(start, end, step):
    if start <= end:
        if step > 0:
            return HyperValue(SeparateSpace(start, end, step))
        else:
            raise ValueError(f'Step value should be positive, but {step} found.')
    else:
        raise ValueError(f'Start value should be no greater tha end value, but {start} > {end} found.')


def choice(chs):
    if isinstance(chs, (list, tuple)):
        if len(chs) > 0:
            return HyperValue(FixedSpace(len(chs))) >> (lambda x: chs[x])
        else:
            raise ValueError(f'At least 1 choice should be contained, but {repr(chs)} found.')
    else:
        raise TypeError(f'List or tuple required, but {repr(chs)} found.')
