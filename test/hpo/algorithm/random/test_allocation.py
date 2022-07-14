import random
from random import _inst as _RANDOM_INST

import pytest

from ditk.hpo.algorithm.random import make_native_random


# noinspection DuplicatedCode
@pytest.mark.unittest
class TestHpoAlgorithmRandomAllocation:

    def test_make_native_random(self):
        r1 = random.Random(233)
        assert make_native_random(r1) is r1

        _first = None
        for _ in range(20):
            r2 = make_native_random(24)
            now = tuple(map(lambda x: r2.randint(0, 100), range(20)))
            if _first is None:
                _first = now
            else:
                assert _first == now, 'Random not stable.'

        assert make_native_random(None) is _RANDOM_INST
        with pytest.raises(TypeError):
            make_native_random('234')
