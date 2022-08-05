import random

import pytest

from lighttuner.hpo import hpo, R, quniform, uniform, M, Skip
from ....testing import no_handlers


@hpo
def opt_func(v):
    x, y = v['x'], v['y']
    if random.random() < 0.45:
        raise ValueError('Fxxk this shxt')  # retry is supported

    return {
        'result': x * y,
        'sum': x + y,
    }


# noinspection DuplicatedCode
@pytest.mark.unittest
class TestHpoAlgorithmBayesAlgorithm:

    @pytest.mark.flaky(reruns=3)
    @no_handlers()
    def test_bayes_single_maximize(self):
        cfg, res, metrics = opt_func.bayes() \
            .max_steps(50) \
            .init_steps(10) \
            .maximize(R['result']) \
            .concern(M['time'], 'time_cost') \
            .concern(R['sum'], 'sum') \
            .spaces(
            {
                'x': uniform(-55, 125),  # continuous space
                'y': quniform(-60, 20, 10),  # integer based space
            }).run()

        assert res['result'] >= 2900
        assert res['result'] == pytest.approx(cfg['x'] * cfg['y'])

    @pytest.mark.flaky(reruns=3)
    def test_bayes_single_maximize_silent(self):
        cfg, res, metrics = opt_func.bayes(silent=True) \
            .max_steps(50) \
            .init_steps(10) \
            .maximize(R['result']) \
            .concern(M['time'], 'time_cost') \
            .concern(R['sum'], 'sum') \
            .spaces(
            {
                'x': uniform(-55, 125),  # continuous space
                'y': quniform(-60, 20, 10),  # integer based space
            }).run()

        assert res['result'] >= 2900
        assert res['result'] == pytest.approx(cfg['x'] * cfg['y'])

    @pytest.mark.flaky(reruns=3)
    def test_bayes_single_minimize(self):
        cfg, res, metrics = opt_func.bayes(silent=True) \
            .max_steps(50) \
            .init_steps(10) \
            .minimize(R['result']) \
            .concern(M['time'], 'time_cost') \
            .concern(R['sum'], 'sum') \
            .spaces(
            {
                'x': uniform(-55, 125),  # continuous space
                'y': quniform(-60, 20, 10),  # integer based space
            }).run()

        assert res['result'] <= -7000
        assert res['result'] == pytest.approx(cfg['x'] * cfg['y'])

    @pytest.mark.flaky(reruns=3)
    def test_bayes_single_maximize_without_init(self):
        cfg, res, metrics = opt_func.bayes(silent=True) \
            .max_steps(50) \
            .init_steps(0) \
            .maximize(R['result']) \
            .concern(M['time'], 'time_cost') \
            .concern(R['sum'], 'sum') \
            .spaces(
            {
                'x': uniform(-55, 125),  # continuous space
                'y': quniform(-60, 20, 10),  # integer based space
            }).run()

        assert res['result'] >= 2900
        assert res['result'] == pytest.approx(cfg['x'] * cfg['y'])

    @pytest.mark.flaky(reruns=3)
    def test_bayes_single_maximize_with_skip(self):

        @hpo
        def funcx(v):
            x, y = v['x'], v['y']
            if random.random() < 0.15:
                raise Skip('Fxxk this shxt', 2, 3)  # without retry

            return {
                'result': x * y,
                'sum': x + y,
            }

        cfg, res, metrics = funcx.bayes(silent=True) \
            .max_steps(50) \
            .maximize(R['result']) \
            .concern(M['time'], 'time_cost') \
            .concern(R['sum'], 'sum') \
            .spaces(
            {
                'x': uniform(-55, 125),  # continuous space
                'y': quniform(-60, 20, 10),  # integer based space
            }).run()

        assert res['result'] >= 2900
        assert res['result'] == pytest.approx(cfg['x'] * cfg['y'])

    def test_bayes_single_maximize_with_condition(self):
        cfg, res, metrics = opt_func.bayes(silent=True) \
            .init_steps(10) \
            .maximize(R['result']) \
            .concern(M['time'], 'time_cost') \
            .concern(R['sum'], 'sum') \
            .stop_when(R['result'] >= 2900) \
            .spaces(
            {
                'x': uniform(-55, 125),  # continuous space
                'y': quniform(-60, 20, 10),  # integer based space
            }).run()

        assert res['result'] >= 2900
        assert res['result'] == pytest.approx(cfg['x'] * cfg['y'])
