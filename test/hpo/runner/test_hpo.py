import pytest

from ditk.hpo import hpo, R
from ditk.hpo.runner.hpo import HpoFunc
from test.hpo.algorithm.base import get_hpo_func


@pytest.mark.unittest
class TestHpoAlgorithmHpo:
    def test_common(self):
        visited, opt = get_hpo_func()
        assert opt({'x': 2, 'y': 3}) == {'result': 6, 'sum': 5}
        assert isinstance(opt, HpoFunc)
        assert repr(opt).startswith('<HpoFunc of <function get_hpo_func.<locals>.opt at')
        assert hpo(opt) is opt

    def test_max_min_syntax(self):
        visited, func = get_hpo_func()
        with pytest.raises(SyntaxError):
            func.random() \
                .max_steps(1000) \
                .minimize(R['result']) \
                .minimize(R['result'])

        with pytest.raises(SyntaxError):
            func.random() \
                .max_steps(1000) \
                .minimize(R['result']) \
                .maximize(R['result'])
