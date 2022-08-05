import random
from random import _inst as _RANDOM_INST

from ...space import BaseSpace, SeparateSpace, ContinuousSpace, FixedSpace


def random_space_value(space: BaseSpace, rnd: random.Random):
    if isinstance(space, SeparateSpace):
        return rnd.randint(0, space.count - 1) * space.step + space.start
    elif isinstance(space, ContinuousSpace):
        return rnd.random() * (space.ubound - space.lbound) + space.lbound
    elif isinstance(space, FixedSpace):
        return rnd.randint(0, space.count - 1)
    else:
        raise TypeError(f'Unknown space type - {repr(space)}.')  # pragma: no cover


def make_native_random(seed) -> random.Random:
    if isinstance(seed, random.Random):
        return seed
    elif isinstance(seed, int):
        return random.Random(seed)
    elif seed is None:
        return _RANDOM_INST
    else:
        raise TypeError(f"Unknown type of random seed - {seed!r}.")  # pragma: no cover
