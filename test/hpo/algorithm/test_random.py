import random
from random import _inst as _RANDOM_INST

import pytest

from ditk.hpo import uniform, quniform, choice, R, hpo, M
from ditk.hpo.algorithm import RandomSearchAlgorithm
from ditk.hpo.algorithm.random import _make_random
from .base import get_hpo_func, EPS
from ...testing import no_handlers


@pytest.mark.unittest
class TestHpoAlgorithmRandom:
    def test_make_random(self):
        r1 = random.Random(233)
        assert _make_random(r1) is r1

        _first = None
        for _ in range(20):
            r2 = _make_random(24)
            now = tuple(map(lambda x: r2.randint(0, 100), range(20)))
            if _first is None:
                _first = now
            else:
                assert _first == now, 'Random not stable.'

        assert _make_random(None) is _RANDOM_INST
        with pytest.raises(TypeError):
            _make_random('234')

    def test_name(self):
        assert RandomSearchAlgorithm.algorithm_name() == 'random search algorithm'

    @no_handlers()
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

    def test_random_silent(self):
        visited, func = get_hpo_func()
        func.random(silent=True).max_steps(1000).spaces({
            'x': uniform(-2, 8),
            'y': 2.5,
        }).run()

        assert len(visited) == 1000
        for item in visited:
            assert -2 <= item['x'] <= 8
            assert item['y'] == pytest.approx(2.5)

    def test_random_all(self):
        visited, func = get_hpo_func()
        func.random(silent=True).max_steps(1000).spaces({
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
        cfg, res, metrics = func.random(silent=True).stop_when(R['result'].abs() <= 0.5).spaces({
            'x': uniform(-2, 8),
            'y': quniform(-1.6, 7.8, 0.2),
        }).run()

        assert pytest.approx(res['result']) == pytest.approx(cfg['x'] * cfg['y'])
        assert abs(res['result']) <= 0.5

    def test_random_stop_when_or(self):
        visited, func = get_hpo_func()
        cfg, res, metrics = func.random(silent=True) \
            .stop_when(R['result'].abs() <= 0.5) \
            .stop_when(R['result'] >= 56.25) \
            .spaces({
            'x': uniform(-2, 8),
            'y': quniform(-1.6, 7.8, 0.2),
        }).run()

        assert pytest.approx(res['result']) == pytest.approx(cfg['x'] * cfg['y'])
        assert (abs(res['result']) <= 0.5) or (res['result'] >= 56.25)

    def test_random_maximize(self):
        visited, func = get_hpo_func()
        cfg, res, metrics = func.random(silent=True) \
            .max_steps(1000) \
            .maximize(R['result']) \
            .spaces({
            'x': uniform(-2, 8),
            'y': quniform(-1.6, 7.8, 0.2),
        }).run()

        assert pytest.approx(res['result']) == pytest.approx(cfg['x'] * cfg['y'])
        assert res['result'] >= 55

    def test_random_minimize(self):
        visited, func = get_hpo_func()
        cfg, res, metrics = func.random(silent=True) \
            .max_steps(1000) \
            .minimize(R['result']) \
            .spaces({
            'x': uniform(-2, 8),
            'y': quniform(-1.6, 7.8, 0.2),
        }).run()

        assert pytest.approx(res['result']) == pytest.approx(cfg['x'] * cfg['y'])
        assert res['result'] <= -12

    def test_random_zero(self):
        visited, func = get_hpo_func()
        assert func.random(silent=True) \
                   .max_steps(0) \
                   .minimize(R['result']) \
                   .spaces({
            'x': uniform(-2, 8),
            'y': quniform(-1.6, 7.8, 0.2),
        }).run() is None

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
            .spaces({
            'x': uniform(-2, 8),
            'y': quniform(-1.6, 7.8, 0.2),
        }).run()

        assert pytest.approx(res['result']) == pytest.approx(cfg['x'] * cfg['y'])
        assert res['result'] <= -12
        result1 = res['result']

        for _ in range(5):
            cfg, res, metrics = func.random(silent=True) \
                .max_steps(1000) \
                .minimize(R['result']) \
                .seed(12) \
                .spaces({
                'x': uniform(-2, 8),
                'y': quniform(-1.6, 7.8, 0.2),
            }).run()

            assert pytest.approx(res['result']) == pytest.approx(cfg['x'] * cfg['y'])
            assert res['result'] == pytest.approx(result1)
