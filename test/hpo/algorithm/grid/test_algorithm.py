import pytest

from lighttuner.hpo.algorithm.grid import GridAlgorithm


# noinspection DuplicatedCode
@pytest.mark.unittest
class TestHpoAlgorithmGridAlgorithm:

    def test_name(self):
        assert GridAlgorithm.algorithm_name() == 'grid algorithm'
