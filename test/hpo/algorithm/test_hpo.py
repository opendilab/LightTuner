import pytest

from ditk.hpo import hpo
from ditk.hpo.algorithm.hpo import HpoFunc
from .base import get_hpo_func


@pytest.mark.unittest
class TestHpoAlgorithmHpo:
    def test_common(self):
        visited, opt = get_hpo_func()
        assert opt({'x': 2, 'y': 3}) == {'result': 6, 'sum': 5}
        assert isinstance(opt, HpoFunc)
        assert repr(opt).startswith('<HpoFunc of <function get_hpo_func.<locals>.opt at')
        assert hpo(opt) is opt
