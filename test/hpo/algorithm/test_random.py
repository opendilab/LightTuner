import pytest

from ditk.hpo import uniform, quniform, choice, R
from ditk.hpo.algorithm import RandomSearchAlgorithm
from .base import get_hpo_func, EPS
from ...testing import init_handlers


@pytest.mark.unittest
class TestHpoAlgorithmRandom:
    @init_handlers([])
    def test_name(self):
        assert RandomSearchAlgorithm.algorithm_name() == 'random search algorithm'

    @init_handlers([])
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

    @init_handlers([])
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

    @init_handlers([])
    def test_random_stop_when(self):
        visited, func = get_hpo_func()
        cfg, res, metrics = func.random().stop_when(R['result'].abs() <= 0.5).spaces({
            'x': uniform(-2, 8),
            'y': quniform(-1.6, 7.8, 0.2),
        }).run()

        assert pytest.approx(res['result']) == pytest.approx(cfg['x'] * cfg['y'])
        assert abs(res['result']) <= 0.5

    @init_handlers([])
    def test_random_stop_when_or(self):
        visited, func = get_hpo_func()
        cfg, res, metrics = func.random() \
            .stop_when(R['result'].abs() <= 0.5) \
            .stop_when(R['result'] >= 56.25) \
            .spaces({
            'x': uniform(-2, 8),
            'y': quniform(-1.6, 7.8, 0.2),
        }).run()

        assert pytest.approx(res['result']) == pytest.approx(cfg['x'] * cfg['y'])
        assert (abs(res['result']) <= 0.5) or (res['result'] >= 56.25)

    @init_handlers([])
    def test_random_maximize(self):
        visited, func = get_hpo_func()
        cfg, res, metrics = func.random() \
            .max_steps(1000) \
            .maximize(R['result']) \
            .spaces({
            'x': uniform(-2, 8),
            'y': quniform(-1.6, 7.8, 0.2),
        }).run()

        assert pytest.approx(res['result']) == pytest.approx(cfg['x'] * cfg['y'])
        assert res['result'] >= 55

    @init_handlers([])
    def test_random_minimize(self):
        visited, func = get_hpo_func()
        cfg, res, metrics = func.random() \
            .max_steps(1000) \
            .minimize(R['result']) \
            .spaces({
            'x': uniform(-2, 8),
            'y': quniform(-1.6, 7.8, 0.2),
        }).run()

        assert pytest.approx(res['result']) == pytest.approx(cfg['x'] * cfg['y'])
        assert res['result'] <= -12

    @init_handlers([])
    def test_random_zero(self):
        visited, func = get_hpo_func()
        assert func.random() \
                   .max_steps(0) \
                   .minimize(R['result']) \
                   .spaces({
            'x': uniform(-2, 8),
            'y': quniform(-1.6, 7.8, 0.2),
        }).run() is None
