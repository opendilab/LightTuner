import pytest

from ditk.hpo.algorithm import RandomAlgorithm


# noinspection DuplicatedCode
@pytest.mark.unittest
class TestHpoAlgorithmRandomAlgorithm:
    def test_name(self):
        assert RandomAlgorithm.algorithm_name() == 'random algorithm'
