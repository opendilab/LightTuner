import random

import pytest

from ditk.hpo import choice, hpo, R, quniform, uniform, M, SkipSample
from ditk.hpo.old_algorithm.bayes.algorithm import hyper_to_bound
from ditk.hpo.space import ContinuousSpace, SeparateSpace
from ditk.hpo.value import HyperValue
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
    def test_hyper_to_bound(self):
        hv1 = HyperValue(ContinuousSpace(0.4, 2.2))
        (lbound, ubound), func = hyper_to_bound(hv1)
        assert lbound == pytest.approx(0.4)
        assert ubound == pytest.approx(2.2)
        assert func(1) == 1
        assert func(2.2) == pytest.approx(2.2)
        assert func(290384.92387) == pytest.approx(290384.92387)

        hv2 = 2 ** (hv1 + 2)
        (lbound, ubound), func = hyper_to_bound(hv2)
        assert lbound == pytest.approx(0.4)
        assert ubound == pytest.approx(2.2)
        assert func(1) == 8
        assert func(2.2) == pytest.approx(18.37917367995256)
        assert func(4.92387) == pytest.approx(121.42065073539287)

        hv3 = HyperValue(SeparateSpace(10.2, 12.4, 0.2))
        (lbound, ubound), func = hyper_to_bound(hv3)
        assert lbound == pytest.approx(0.0)
        assert ubound == pytest.approx(12.0)
        assert func(1) == pytest.approx(10.4)
        assert func(2.2) == pytest.approx(10.6)
        assert func(4.92387) == pytest.approx(11.0)
        assert func(12.0) == pytest.approx(12.4)

        hv4 = 2 ** (hv3 + 1)
        (lbound, ubound), func = hyper_to_bound(hv4)
        assert lbound == pytest.approx(0.0)
        assert ubound == pytest.approx(12.0)
        assert func(1) == pytest.approx(2702.3522012628846)
        assert func(2.2) == pytest.approx(3104.1875282132946)
        assert func(4.92387) == pytest.approx(4096.0)
        assert func(12.0) == pytest.approx(10809.408805051538)

        hv5 = choice(['a', 'b', 'c'])
        with pytest.raises(TypeError):
            hyper_to_bound(hv5)

    @pytest.mark.flaky(reruns=3)
    @no_handlers()
    def test_bayes_single_maximize(self):
        cfg, res, metrics = opt_func.bayes() \
            .max_steps(30) \
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
            .max_steps(30) \
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
            .max_steps(30) \
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
            .max_steps(30) \
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
                raise SkipSample('Fxxk this shxt', 2, 3)  # without retry

            return {
                'result': x * y,
                'sum': x + y,
            }

        cfg, res, metrics = funcx.bayes(silent=True) \
            .max_steps(30) \
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

    def test_bayes_single_maximize_with_seed(self):
        @hpo
        def funcx(v):
            x, y = v['x'], v['y']

            return {
                'result': x * y,
                'sum': x + y,
            }

        cfg, res, metrics = funcx.bayes(silent=True) \
            .max_steps(20) \
            .maximize(R['result']) \
            .concern(M['time'], 'time_cost') \
            .concern(R['sum'], 'sum') \
            .seed(12) \
            .spaces(
            {
                'x': uniform(-55, 125),  # continuous space
                'y': quniform(-60, 20, 10),  # integer based space
            }).run()

        assert res['result'] == pytest.approx(cfg['x'] * cfg['y'])
        result1 = res['result']

        for _ in range(2):
            cfg, res, metrics = funcx.bayes(silent=True) \
                .max_steps(20) \
                .maximize(R['result']) \
                .concern(M['time'], 'time_cost') \
                .concern(R['sum'], 'sum') \
                .seed(12) \
                .spaces(
                {
                    'x': uniform(-55, 125),  # continuous space
                    'y': quniform(-60, 20, 10),  # integer based space
                }).run()

            assert res['result'] == pytest.approx(result1)
            assert res['result'] == pytest.approx(cfg['x'] * cfg['y'])
