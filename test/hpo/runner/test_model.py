import pytest

from ditk.hpo.algorithm import Task
from ditk.hpo.runner.model import RunResult, R, M, C, RunFailed, RunSkipped
from ditk.hpo.runner.signal import Skip


@pytest.mark.unittest
class TestHpoRunnerModel:

    def test_run_result(self):
        r1 = RunResult(
            Task(1, {
                'a': 1,
                'b': [2, 3]
            }, ()),
            {
                'aa': 4,
                'bb': [5, 6]
            },
            {'time': 3.1415926535},
            R,
        )

        assert r1.task_id == 1
        assert r1.config == {'a': 1, 'b': [2, 3]}
        assert r1.retval == {'aa': 4, 'bb': [5, 6]}
        assert r1.metrics == pytest.approx({'time': 3.1415926535})
        assert r1.value == {'aa': 4, 'bb': [5, 6]}
        assert r1.get(R['aa']) == 4
        assert r1.get(R['bb'][0]) == 5
        assert r1.get(R['bb'][1]) == 6
        assert r1.get(M['time']) == pytest.approx(3.1415926535)
        assert r1.get(C['b'][0] * R['bb'][1]) == 12
        assert repr(r1) == "<RunResult task_id: 1, value: {'aa': 4, 'bb': [5, 6]}>"

        r2 = RunResult(
            Task(2, {
                'a': 1,
                'b': [2, 3]
            }, ('abcdefg', )),
            {
                'aa': 4,
                'bb': [5, 6, 7, 10]
            },
            {'time': 3.1415926535},
            R['bb'].mean(),
        )
        assert r2.task_id == 2
        assert r2.config == {'a': 1, 'b': [2, 3]}
        assert r2.retval == {'aa': 4, 'bb': [5, 6, 7, 10]}
        assert r2.metrics == pytest.approx({'time': 3.1415926535})
        assert r2.value == pytest.approx(7.0)
        assert r2.get(R['aa']) == 4
        assert r2.get(R['bb'][0]) == 5
        assert r2.get(R['bb'][1]) == 6
        assert r2.get(M['time']) == pytest.approx(3.1415926535)
        assert r2.get(C['b'][0] * R['bb'][1]) == 12
        assert repr(r2) == "<RunResult task_id: 2, value: 7.0>"

    def test_run_failed(self):
        rf = RunFailed(
            Task(1, {
                'a': 1,
                'b': [2, 3]
            }, ()),
            ValueError('abcd', 233),
            {'time': 3.1415926535},
        )
        assert isinstance(rf, Exception)
        assert rf.task_id == 1
        assert rf.config == {'a': 1, 'b': [2, 3]}
        assert type(rf.error) == ValueError
        assert rf.error.args == ('abcd', 233)
        assert rf.args == (ValueError, 'abcd', 233)
        assert rf.metrics == pytest.approx({'time': 3.1415926535})

    def test_run_skip(self):
        rk = RunSkipped(
            Task(1, {
                'a': 1,
                'b': [2, 3]
            }, ()),
            Skip('abcd', 233),
            {'time': 3.1415926535},
        )
        assert isinstance(rk, Exception)
        assert rk.task_id == 1
        assert rk.config == {'a': 1, 'b': [2, 3]}
        assert rk.args == ('abcd', 233)
        assert rk.metrics == pytest.approx({'time': 3.1415926535})
