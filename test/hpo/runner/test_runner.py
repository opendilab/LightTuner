from typing import Any, Tuple, Iterable

import pytest

from ditk.hpo import uniform, Skip
from ditk.hpo.algorithm import BaseAlgorithm, BaseSession, Task
from ditk.hpo.runner.event import RunnerEventSet
from ditk.hpo.runner.model import R, RunSkipped, RunFailed, RunResult
from ditk.hpo.runner.result import _ResultExpression
from ditk.hpo.runner.runner import ParallelSearchRunner
from ditk.hpo.utils import ThreadService, RankList, ServiceNoLongerAccept


class _MyAlgorithm(BaseAlgorithm):
    def __init__(self, v, even_only=False, **kwargs):
        BaseAlgorithm.__init__(self, **kwargs)
        self.v = v
        self.even_only = even_only

    def get_session(self, space, service: ThreadService) -> '_MySession':
        return _MySession(self, space, service)


class _MySession(BaseSession):
    def __init__(self, algorithm: _MyAlgorithm, space, service: ThreadService):
        BaseSession.__init__(self, space, service)
        self.__algorithm = algorithm
        self.errlist = []
        self.reslist = []

    def _return_on_success(self, task: Task, retval: Any):
        self.reslist.append((task, retval))

    def _return_on_failed(self, task: Task, error: Exception):
        self.errlist.append((task, type(error), error.args))

    def _run(self):
        for i in range(self.__algorithm.v):
            if self.__algorithm.even_only and i % 2 == 1:
                raise ValueError(f'Even only, but {i} found.')
            try:
                self._put_via_space(tuple(i for _ in range(len(self.vsp))), ('this is attachment', i))
            except ServiceNoLongerAccept:
                pass


class _MyEventSet(RunnerEventSet):
    def __init__(self):
        self.is_initialized = False
        self.is_started = False
        self.is_completed = False

        self.step_count = 0
        self.ok_count = 0
        self.skip_count = 0
        self.fail_count = 0
        self.complete_count = 0

    def init_ok(self, target_name: str, params: Iterable[Tuple[str, _ResultExpression]],
                concerns: Iterable[Tuple[str, _ResultExpression]]):
        self.is_initialized = True

    def run_start(self):
        self.is_started = True

    def run_complete(self, is_cond_meet: bool):
        self.is_completed = True

    def step(self, task: Task):
        self.step_count += 1

    def step_ok(self, task: Task, result: RunResult):
        self.ok_count += 1

    def step_fail(self, task: Task, error: RunFailed):
        self.fail_count += 1

    def step_skip(self, task: Task, error: RunSkipped):
        self.skip_count += 1

    def step_final(self, task: Task, ranklist: RankList):
        self.complete_count += 1


# noinspection DuplicatedCode
@pytest.mark.unittest
class TestHpoRunnerRunner:
    def test_simple(self):
        def _my_func(v):
            a, (b0, b1) = v['a'], v['b']
            return (a - 5) ** 2

        runner = ParallelSearchRunner(_MyAlgorithm, _my_func, silent=True)
        _cfg, _res, _metrics = runner \
            .maximize(R) \
            .v(12) \
            .spaces({
                'a': uniform(0, 10),  # these uniform spaces are only placeholders here
                'b': (
                    uniform(0, 10),
                    uniform(0, 10),
                )
            }).run()

        assert _cfg == {'a': 11, 'b': (11, 11)}
        assert _res == 36
        assert 'time' in _metrics

    def test_no_target_error(self):
        # noinspection PyUnusedLocal
        def _my_func(v):
            a, (b0, b1) = v['a'], v['b']
            return (a - 5) ** 2

        runner = ParallelSearchRunner(_MyAlgorithm, _my_func, silent=True)
        with pytest.raises(SyntaxError):
            _cfg, _res, _metrics = runner \
                .v(12) \
                .spaces({
                    'a': uniform(0, 10),  # these uniform spaces are only placeholders here
                    'b': (
                        uniform(0, 10),
                        uniform(0, 10),
                    )
                }).run()

    def test_skip_fail_event(self):
        def _my_func(v):
            a, (b0, b1) = v['a'], v['b']
            if a % 3 == 0:
                raise ValueError(f'Invalid a - {a}', a)
            elif a % 7 == 0:
                raise Skip('skipped', a)
            else:
                return {
                    'result': (a - 32.8) ** 2,
                    'sum': a + b0 + b1,
                }

        runner = ParallelSearchRunner(_MyAlgorithm, _my_func, silent=True)
        _my_event = _MyEventSet()
        _cfg, _res, _metrics = runner \
            .add_event_set(_my_event) \
            .minimize(R['result']) \
            .v(40) \
            .spaces({
                'a': uniform(0, 10),  # these uniform spaces are only placeholders here
                'b': (
                    uniform(0, 10),
                    uniform(0, 10),
                )
            }).run()

        assert _cfg == {'a': 32, 'b': (32, 32)}
        assert _res == pytest.approx({
            'result': 0.64,
            'sum': 96,
        })
        assert 'time' in _metrics

        assert _my_event.is_initialized
        assert _my_event.is_started
        assert _my_event.is_completed

        assert _my_event.step_count == 40
        assert _my_event.ok_count == 22
        assert _my_event.fail_count == 14
        assert _my_event.skip_count == 4
        assert _my_event.complete_count == 40

    def test_condition(self):
        def _my_func(v):
            a, (b0, b1) = v['a'], v['b']
            return {
                'result': (a - 32.8) ** 2,
                'sum': a + b0 + b1,
            }

        runner = ParallelSearchRunner(_MyAlgorithm, _my_func, silent=True)
        _my_event = _MyEventSet()
        _cfg, _res, _metrics = runner \
            .add_event_set(_my_event) \
            .stop_when(R['result'] < 4) \
            .minimize(R['result']) \
            .max_workers(1) \
            .v(40) \
            .spaces({
                'a': uniform(0, 10),  # these uniform spaces are only placeholders here
                'b': (
                    uniform(0, 10),
                    uniform(0, 10),
                )
            }).run()

        assert _cfg == {'a': 31, 'b': (31, 31)}
        assert _res == pytest.approx({
            'result': 3.24,
            'sum': 93,
        })
        assert 'time' in _metrics

    def test_zero(self):
        def _my_func(v):
            a, (b0, b1) = v['a'], v['b']
            return {
                'result': (a - 32.8) ** 2,
                'sum': a + b0 + b1,
            }

        runner = ParallelSearchRunner(_MyAlgorithm, _my_func, silent=True)
        _my_event = _MyEventSet()
        _return = runner \
            .add_event_set(_my_event) \
            .stop_when(R['result'] < 4) \
            .minimize(R['result']) \
            .v(0) \
            .spaces({
                'a': uniform(0, 10),  # these uniform spaces are only placeholders here
                'b': (
                    uniform(0, 10),
                    uniform(0, 10),
                )
            }).run()

        assert _return is None

    def test_invalid_max_workers(self):
        def _my_func(v):
            a, (b0, b1) = v['a'], v['b']
            return {
                'result': (a - 32.8) ** 2,
                'sum': a + b0 + b1,
            }

        runner = ParallelSearchRunner(_MyAlgorithm, _my_func, silent=True)
        _my_event = _MyEventSet()
        with pytest.raises(ValueError):
            _return = runner.max_workers('dfksj')
