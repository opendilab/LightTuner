from .value import HyperValue
from ..space import ContinuousSpace, SeparateSpace, FixedSpace


def uniform(lbound, rbound):
    return HyperValue(ContinuousSpace(lbound, rbound))


def quniform(start, end, step):
    return HyperValue(SeparateSpace(start, end, step))


def choice(chs):
    mapping = list(chs)
    return HyperValue(FixedSpace(len(mapping))) >> (lambda x: mapping[x])
