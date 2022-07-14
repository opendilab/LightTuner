import random

import pytest

from ditk.hpo import R, randint, quniform, choice, uniform, hpo, M
from ..public import get_hpo_func, EPS
from ....testing import no_handlers


# noinspection DuplicatedCode
@pytest.mark.unittest
class TestHpoAlgorithmGridActual:

    @no_handlers()
    def test_grid_unlimited(self):
        visited, opt = get_hpo_func()
        cfg, ret, metrics = opt.grid() \
            .minimize(R['result']) \
            .spaces(
            {
                'x': randint(-10, 100),
                'y': quniform(-10, 20, 30),
                'z': choice(['a', 'b', 'c', 'd', 'e']),
            }
        ).run()

        assert len(visited) == 1110
        for item in visited:
            assert isinstance(item['x'], int)
            assert -10 <= item['x'] <= 100
            assert -10 - EPS <= item['y'] <= 20 + EPS
            assert item['z'] in {'a', 'b', 'c', 'd', 'e'}

        assert cfg['x'] * cfg['y'] == pytest.approx(ret['result'])
        assert cfg['x'] + cfg['y'] == pytest.approx(ret['sum'])
        assert ret['result'] <= -1000

    def test_grid_unlimited_silent(self):
        visited, opt = get_hpo_func()
        cfg, ret, metrics = opt.grid(silent=True) \
            .minimize(R['result']) \
            .spaces(
            {
                'x': randint(-10, 100),
                'y': quniform(-10, 20, 30),
                'z': choice(['a', 'b', 'c', 'd', 'e']),
            }
        ).run()

        assert len(visited) == 1110
        for item in visited:
            assert isinstance(item['x'], int)
            assert -10 <= item['x'] <= 100
            assert -10 - EPS <= item['y'] <= 20 + EPS
            assert item['z'] in {'a', 'b', 'c', 'd', 'e'}

        assert cfg['x'] * cfg['y'] == pytest.approx(ret['result'])
        assert cfg['x'] + cfg['y'] == pytest.approx(ret['sum'])
        assert ret['result'] <= -1000

    def test_grid_weak_limited(self):
        visited, opt = get_hpo_func()
        cfg, ret, metrics = opt.grid(silent=True) \
            .max_steps(10000) \
            .minimize(R['result']) \
            .spaces(
            {
                'x': randint(-10, 100),
                'y': quniform(-10, 20, 30),
                'z': choice(['a', 'b', 'c', 'd', 'e']),
            }
        ).run()

        assert len(visited) == 1110
        for item in visited:
            assert isinstance(item['x'], int)
            assert -10 <= item['x'] <= 100
            assert -10 - EPS <= item['y'] <= 20 + EPS
            assert item['z'] in {'a', 'b', 'c', 'd', 'e'}

        assert cfg['x'] * cfg['y'] == pytest.approx(ret['result'])
        assert cfg['x'] + cfg['y'] == pytest.approx(ret['sum'])
        assert ret['result'] <= -1000

    def test_grid_limited_1(self):
        visited, opt = get_hpo_func()
        cfg, ret, metrics = opt.grid(silent=True) \
            .max_steps(1000) \
            .minimize(R['result']) \
            .spaces(
            {
                'x': uniform(-10, 100),
                'y': uniform(-10, 20),
                'z': choice(['a', 'b', 'c', 'd', 'e']),
            }
        ).run()

        assert len(visited) == 945
        for item in visited:
            assert -10 <= item['x'] <= 100
            assert -10 - EPS <= item['y'] <= 20 + EPS
            assert item['z'] in {'a', 'b', 'c', 'd', 'e'}

        assert cfg['x'] * cfg['y'] == pytest.approx(ret['result'])
        assert cfg['x'] + cfg['y'] == pytest.approx(ret['sum'])
        assert ret['result'] <= -1000

    def test_grid_limited_2(self):
        visited, opt = get_hpo_func()
        cfg, ret, metrics = opt.grid(silent=True) \
            .max_steps(1000) \
            .minimize(R['result']) \
            .spaces(
            {
                'x': uniform(-10, 100),
                'y': quniform(-10, 20, 30),
                'z': choice(['a', 'b', 'c', 'd', 'e']),
            }
        ).run()

        assert len(visited) == 1000
        for item in visited:
            assert -10 <= item['x'] <= 100
            assert -10 - EPS <= item['y'] <= 20 + EPS
            assert item['z'] in {'a', 'b', 'c', 'd', 'e'}

        assert cfg['x'] * cfg['y'] == pytest.approx(ret['result'])
        assert cfg['x'] + cfg['y'] == pytest.approx(ret['sum'])
        assert ret['result'] <= -1000

    def test_grid_limited_3(self):
        visited, opt = get_hpo_func()
        cfg, ret, metrics = opt.grid(silent=True) \
            .max_steps(11) \
            .minimize(R['result']) \
            .spaces(
            {
                'x': uniform(-10, 100),
                'y': quniform(-10, 20, 30),
                'z': choice(['a', 'b', 'c', 'd', 'e']),
            }
        ).run()

        assert len(visited) == 10
        for item in visited:
            assert -10 <= item['x'] <= 100
            assert -10 - EPS <= item['y'] <= 20 + EPS
            assert item['z'] in {'a', 'b', 'c', 'd', 'e'}

        assert cfg['x'] * cfg['y'] == pytest.approx(ret['result'])
        assert cfg['x'] + cfg['y'] == pytest.approx(ret['sum'])
        assert ret['result'] <= -1000

    def test_error_unlimited(self):
        visited, opt = get_hpo_func()
        with pytest.raises(ValueError):
            opt.grid(silent=True) \
                .minimize(R['result']) \
                .spaces(
                {
                    'x': uniform(-10, 100),
                    'y': uniform(-10, 20),
                    'z': choice(['a', 'b', 'c', 'd', 'e']),
                }
            ).run()

    @pytest.mark.flaky(reruns=3)
    def test_grid_with_error(self):

        @hpo
        def opt_func(v):
            x, y = v['x'], v['y']
            if random.random() < 0.5:
                raise ValueError('Fxxk this shxt')  # retry is supported

            return {
                'result': x * y,
                'sum': x + y,
            }

        cfg, res, metrics = opt_func.grid(silent=True) \
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

    def test_grid_stop_when_or(self):
        visited, func = get_hpo_func()
        cfg, res, metrics = func.grid() \
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
