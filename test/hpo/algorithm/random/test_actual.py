import random

import pytest

from ditk.hpo import uniform, quniform, choice, R, hpo, M
from ..base import get_hpo_func, EPS
from ....testing import no_handlers


# noinspection DuplicatedCode
@pytest.mark.unittest
class TestHpoAlgorithmRandomActual:
    @no_handlers()
    def test_random_single(self):
        visited, func = get_hpo_func()
        func.random().max_steps(1000).maximize(R['result']).spaces({
            'x': uniform(-2, 8),
            'y': 2.5,
        }).run()

        assert len(visited) == 1000
        for item in visited:
            assert -2 <= item['x'] <= 8
            assert item['y'] == pytest.approx(2.5)

    def test_random_silent(self):
        visited, func = get_hpo_func()
        func.random(silent=True).max_steps(1000).maximize(R['result']).spaces({
            'x': uniform(-2, 8),
            'y': 2.5,
        }).run()

        assert len(visited) == 1000
        for item in visited:
            assert -2 <= item['x'] <= 8
            assert item['y'] == pytest.approx(2.5)

    def test_random_all(self):
        visited, func = get_hpo_func()
        func.random(silent=True).max_steps(1000).maximize(R['result']).spaces({
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
        cfg, res, metrics = func.random() \
            .minimize(R['result'].abs()) \
            .stop_when(R['result'].abs() <= 0.5) \
            .spaces(
            {
                'x': uniform(0.15, 4),
                'y': quniform(1.8, 3.8, 0.2),
            }
        ).run()

        assert pytest.approx(res['result']) == pytest.approx(cfg['x'] * cfg['y'])
        assert abs(res['result']) <= 0.5

    def test_random_stop_when_or(self):
        visited, func = get_hpo_func()
        cfg, res, metrics = func.random() \
            .maximize(R['result']) \
            .stop_when(R['sum'] <= -4.9) \
            .stop_when(R['sum'] >= 4.9) \
            .spaces(
            {
                'x': quniform(-2.5, 2.5, 1.0),
                'y': quniform(-2.5, 2.5, 1.0),
            }
        ).run()

        assert pytest.approx(res['result']) == pytest.approx(cfg['x'] * cfg['y'])
        assert res['sum'] <= -4.9 or res['sum'] >= 4.9

    def test_random_maximize(self):
        visited, func = get_hpo_func()
        cfg, res, metrics = func.random(silent=True) \
            .max_steps(1000) \
            .maximize(R['result']) \
            .spaces(
            {
                'x': uniform(-2, 8),
                'y': quniform(-1.6, 7.8, 0.2),
            }
        ).run()

        assert pytest.approx(res['result']) == pytest.approx(cfg['x'] * cfg['y'])
        assert res['result'] >= 55

    def test_random_minimize(self):
        visited, func = get_hpo_func()
        cfg, res, metrics = func.random(silent=True) \
            .max_steps(1000) \
            .minimize(R['result']) \
            .spaces(
            {
                'x': uniform(-2, 8),
                'y': quniform(-1.6, 7.8, 0.2),
            }
        ).run()

        assert pytest.approx(res['result']) == pytest.approx(cfg['x'] * cfg['y'])
        assert res['result'] <= -12

    def test_random_zero(self):
        visited, func = get_hpo_func()
        assert func.random(silent=True) \
                   .max_steps(0) \
                   .minimize(R['result']) \
                   .spaces(
            {
                'x': uniform(-2, 8),
                'y': quniform(-1.6, 7.8, 0.2),
            }
        ).run() is None

    @pytest.mark.flaky(reruns=3)
    def test_random_with_error(self):
        @hpo
        def opt_func(v):
            x, y = v['x'], v['y']
            if random.random() < 0.5:
                raise ValueError('Fxxk this shxt')  # retry is supported

            return {
                'result': x * y,
                'sum': x + y,
            }

        cfg, res, metrics = opt_func.random(silent=True) \
            .max_steps(1000) \
            .maximize(R['result']) \
            .concern(M['time'], 'time_cost') \
            .concern(R['sum'], 'sum') \
            .spaces(  # search spaces
            {
                'x': uniform(-55, 125),  # continuous space
                'y': quniform(-60, 20, 10),  # integer based space
            }
        ).run()

        assert pytest.approx(res['result']) == pytest.approx(cfg['x'] * cfg['y'])
        assert res['result'] >= 3000

    def test_random_minimize_with_seed(self):
        visited, func = get_hpo_func()
        cfg, res, metrics = func.random(silent=True) \
            .max_steps(1000) \
            .minimize(R['result']) \
            .seed(12) \
            .spaces(
            {
                'x': uniform(-2, 8),
                'y': quniform(-1.6, 7.8, 0.2),
            }
        ).run()

        assert pytest.approx(res['result']) == pytest.approx(cfg['x'] * cfg['y'])
        assert res['result'] <= -12
        result1 = res['result']

        for _ in range(5):
            cfg, res, metrics = func.random(silent=True) \
                .max_steps(1000) \
                .minimize(R['result']) \
                .seed(12) \
                .spaces(
                {
                    'x': uniform(-2, 8),
                    'y': quniform(-1.6, 7.8, 0.2),
                }
            ).run()

            assert pytest.approx(res['result']) == pytest.approx(cfg['x'] * cfg['y'])
            assert res['result'] == pytest.approx(result1)
