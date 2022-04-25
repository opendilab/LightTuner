import pytest

from ditk.hpo import uniform, quniform, choice, R
from .base import get_hpo_func, EPS


@pytest.mark.unittest
class TestHpoAlgorithmRandom:
    def test_random_single(self):
        visited, func = get_hpo_func()
        func.random().max_steps(1000).spaces({
            'x': uniform(-2, 8),
            'y': 2.5,
        }).run()

        assert len(visited) == 1000
        for item in visited:
            assert -2 <= item['x'] <= 8
            assert item['y'] == pytest.approx(2.5)

    def test_random_all(self):
        visited, func = get_hpo_func()
        func.random().max_steps(1000).spaces({
            'x': uniform(-2, 8),
            'y': quniform(-1.6, 7.8, 0.2),
            'z': choice(['a', 'b', 'c'])
        }).run()

        assert len(visited) == 1000
        for item in visited:
            assert -2 <= item['x'] <= 8
            assert -1.6 - EPS <= item['y'] <= 7.8 + EPS
            index = (item['y'] - (-1.6)) / 0.2
            assert abs(round(index) - index) == pytest.approx(0.0)
            assert item['z'] in {'a', 'b', 'c'}

    def test_random_stop_when(self):
        visited, func = get_hpo_func()
        func.random().stop_when(R['result'].abs() <= 0.5).spaces({
            'x': uniform(-2, 8),
            'y': quniform(-1.6, 7.8, 0.2),
        }).run()

        last_item = visited[-1]
        assert abs(last_item['x'] * last_item['y']) <= 0.5

    def test_random_stop_when_or(self):
        visited, func = get_hpo_func()
        func.random() \
            .stop_when(R['result'].abs() <= 0.5) \
            .stop_when(R['result'] >= 56.25) \
            .spaces({
            'x': uniform(-2, 8),
            'y': quniform(-1.6, 7.8, 0.2),
        }).run()

        last_item = visited[-1]
        assert (abs(last_item['x'] * last_item['y']) <= 0.5) or (last_item['x'] * last_item['y'] >= 56.25)
