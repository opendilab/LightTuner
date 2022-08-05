import pytest

from lighttuner.hpo.algorithm.base import Task, OptimizeDirection


@pytest.mark.unittest
class TestHpoAlgorithmBaseModel:

    def test_task(self):
        t = Task(1, {'a': 1, 'b': [2, 3]}, ([1, 2, 3], ))
        assert t.task_id == 1
        assert t.config == {'a': 1, 'b': [2, 3]}
        assert t.attachment == ([1, 2, 3], )

    def test_optimize_direction(self):
        assert OptimizeDirection.loads('minimize') == OptimizeDirection.MINIMIZE
        assert OptimizeDirection.loads('Maximize') == OptimizeDirection.MAXIMIZE
