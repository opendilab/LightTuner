import pytest

from lighttuner.hpo.algorithm.bayes import BayesAlgorithm


# noinspection DuplicatedCode
@pytest.mark.unittest
class TestHpoAlgorithmBayesAlgorithm:

    def test_name(self):
        assert BayesAlgorithm.algorithm_name() == 'bayes algorithm'
