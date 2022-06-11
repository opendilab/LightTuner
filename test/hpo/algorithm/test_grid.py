import random

import pytest

from ditk.hpo import R, randint, quniform, choice, uniform, hpo, M
from ditk.hpo.algorithm.grid import allocate_continuous, allocate_separate, allocate_fixed, GridSearchAlgorithm
from ditk.hpo.space import ContinuousSpace, SeparateSpace, FixedSpace
from .base import get_hpo_func, EPS
from ...testing import no_handlers


# noinspection DuplicatedCode
@pytest.mark.unittest
class TestHpoAlgorithmGrid:
    @no_handlers()
    def test_allocate_continuous(self):
        space = ContinuousSpace(0.4, 2.2)
        assert allocate_continuous(space, 0) == pytest.approx(())
        assert allocate_continuous(space, 1) == pytest.approx((1.3,))
        assert allocate_continuous(space, 2) == pytest.approx((0.4, 2.2))
        assert allocate_continuous(space, 3) == pytest.approx((0.4, 1.3, 2.2))
        assert allocate_continuous(space, 4) == pytest.approx((0.4, 1.0, 1.6, 2.2))
        assert allocate_continuous(space, 5) == pytest.approx((0.4, 0.85, 1.3, 1.75, 2.2))
        assert allocate_continuous(space, 6) == pytest.approx((0.4, 0.76, 1.12, 1.48, 1.84, 2.2))
        assert allocate_continuous(space, 7) == pytest.approx((0.4, 0.7, 1.0, 1.3, 1.6, 1.9, 2.2))
        assert allocate_continuous(space, 8) == pytest.approx(
            (0.4, 0.6571428571428573, 0.9142857142857144, 1.1714285714285715,
             1.4285714285714288, 1.685714285714286, 1.942857142857143, 2.2))
        assert allocate_continuous(space, 9) == pytest.approx((0.4, 0.625, 0.85, 1.075, 1.3, 1.525, 1.75, 1.975, 2.2))
        assert allocate_continuous(space, 10) == pytest.approx((0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2))
        assert allocate_continuous(space, 11) == pytest.approx(
            (0.4, 0.58, 0.76, 0.94, 1.12, 1.3, 1.48, 1.66, 1.84, 2.02, 2.2))

    @no_handlers()
    def test_allocate_separate(self):
        space = SeparateSpace(0.4, 2.2, 0.2)
        assert allocate_separate(space, 0) == pytest.approx(())
        assert allocate_separate(space, 1) == pytest.approx((1.2,))
        assert allocate_separate(space, 2) == pytest.approx((0.4, 2.2))
        assert allocate_separate(space, 3) == pytest.approx((0.4, 1.2, 2.2))
        assert allocate_separate(space, 4) == pytest.approx((0.4, 1.0, 1.6, 2.2))
        assert allocate_separate(space, 5) == pytest.approx((0.4, 0.8, 1.2, 1.8, 2.2))
        assert allocate_separate(space, 6) == pytest.approx((0.4, 0.8, 1.2, 1.4, 1.8, 2.2))
        assert allocate_separate(space, 7) == pytest.approx((0.4, 0.8, 1.0, 1.2, 1.6, 2.0, 2.2))
        assert allocate_separate(space, 8) == pytest.approx((0.4, 0.6, 1.0, 1.2, 1.4, 1.6, 2.0, 2.2))
        assert allocate_separate(space, 9) == pytest.approx((0.4, 0.6, 0.8, 1.0, 1.2, 1.6, 1.8, 2.0, 2.2))
        assert allocate_separate(space, 10) == pytest.approx((0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2))
        assert allocate_separate(space, 11) == pytest.approx((0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2))
        assert allocate_separate(space, 15) == pytest.approx((0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2))
        assert allocate_separate(space, 100) == pytest.approx((0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2))

    @no_handlers()
    def test_name(self):
        assert GridSearchAlgorithm.algorithm_name() == 'grid search algorithm'

    @no_handlers()
    def test_allocate_fixed(self):
        space = FixedSpace(5)
        assert allocate_fixed(space) == (0, 1, 2, 3, 4)

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

    @no_handlers()
    def test_grid_weak_limited(self):
        visited, opt = get_hpo_func()
        cfg, ret, metrics = opt.grid() \
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

    @no_handlers()
    def test_grid_limited_1(self):
        visited, opt = get_hpo_func()
        cfg, ret, metrics = opt.grid() \
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

    @no_handlers()
    def test_grid_limited_2(self):
        visited, opt = get_hpo_func()
        cfg, ret, metrics = opt.grid() \
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

    @no_handlers()
    def test_grid_limited_3(self):
        visited, opt = get_hpo_func()
        cfg, ret, metrics = opt.grid() \
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

    @no_handlers()
    def test_error_unlimited(self):
        visited, opt = get_hpo_func()
        with pytest.raises(ValueError):
            opt.grid() \
                .minimize(R['result']) \
                .spaces(
                {
                    'x': uniform(-10, 100),
                    'y': uniform(-10, 20),
                    'z': choice(['a', 'b', 'c', 'd', 'e']),
                }
            ).run()

    @pytest.mark.flaky(reruns=3)
    @no_handlers()
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

        cfg, res, metrics = opt_func.grid() \
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
