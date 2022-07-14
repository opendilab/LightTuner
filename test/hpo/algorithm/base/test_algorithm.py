from typing import Any

import pytest

from ditk.hpo import uniform
from ditk.hpo.algorithm.base import BaseConfigure, Task, BaseAlgorithm, BaseSession, SessionState
from ditk.hpo.utils import ThreadService, Result
from ditk.hpo.utils.service import ServiceState


class _TestThreadService(ThreadService):

    def __init__(self, func, max_workers=None):
        ThreadService.__init__(self, max_workers)
        self._func = func

    def _check_recv(self, task: Task):
        pass

    def _before_exec(self, task: Task):
        pass

    def _exec(self, task: Task) -> object:
        _id, _config, _attachment = task
        return self._func(_config)

    def _after_exec(self, task: Task, result: Result):
        pass

    def _after_sentback(self, task: Task, result: Result):
        pass

    def _after_callback(self, task: Task, result: Result):
        pass


class _MyAlgorithm(BaseAlgorithm):

    def __init__(self, v, even_only=False):
        BaseAlgorithm.__init__(self)
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
            self._put_via_space(tuple(i for _ in range(len(self.vsp))), ('this is attachment', i))


# noinspection DuplicatedCode
@pytest.mark.unittest
class TestHpoAlgorithmBaseAlgorithm:

    def test_base_configure(self):
        d1 = {}
        c1 = BaseConfigure(d1)
        assert c1._settings == {}
        d1['a'] = 1
        assert c1._settings == {}

        d2 = {'a': 2, 'b': 3}
        c2 = BaseConfigure(d2)
        assert c2._settings == {'a': 2, 'b': 3}
        d2['a'] = 1
        assert c2._settings == {'a': 2, 'b': 3}

        c3 = BaseConfigure()
        assert c3._settings == {}

    def test_base_configure_actual_use(self):

        class MyBaseConfig(BaseConfigure):

            def seed(self, s: int):
                self._settings['seed'] = s
                return self

        c1 = MyBaseConfig()
        c1.seed(1)
        c1._settings = {'seed': 1}
        c1.seed(2).seed(10)
        c1._settings = {'seed': 10}

    def test_base_algorithm_name(self):
        assert _MyAlgorithm.algorithm_name() == 'my algorithm'

    def test_base_algorithm_object(self):
        algo1 = _MyAlgorithm(10)
        assert algo1.v == 10
        assert not algo1.even_only

        algo2 = _MyAlgorithm(11, True)
        assert algo2.v == 11
        assert algo2.even_only

    @pytest.mark.timeout(10)
    def test_base_algorithm_get_session(self):

        def _my_func(v):
            a, (b0, b1) = v['a'], v['b']
            return (a + b0) ** b1

        _service1 = _TestThreadService(_my_func)
        _session1 = _MyAlgorithm(10).get_session(
            {
                'a': uniform(0, 10),  # these uniform spaces are only placeholders here
                'b': (
                    uniform(0, 10),
                    uniform(0, 10),
                )
            },
            _service1
        )

        try:
            _service1.start()
            _session1.start()
        finally:
            _session1.join()
            _service1.shutdown(wait=True)

        assert _service1.state == ServiceState.DEAD
        assert _service1.error is None
        assert _session1.state == SessionState.DEAD
        assert _session1.error is None

        assert sorted(_session1.reslist) == [
            (Task(1, {
                'a': 0,
                'b': (0, 0)
            }, ('this is attachment', 0)), 1),
            (Task(2, {
                'a': 1,
                'b': (1, 1)
            }, ('this is attachment', 1)), 2),
            (Task(3, {
                'a': 2,
                'b': (2, 2)
            }, ('this is attachment', 2)), 16),
            (Task(4, {
                'a': 3,
                'b': (3, 3)
            }, ('this is attachment', 3)), 216),
            (Task(5, {
                'a': 4,
                'b': (4, 4)
            }, ('this is attachment', 4)), 4096),
            (Task(6, {
                'a': 5,
                'b': (5, 5)
            }, ('this is attachment', 5)), 100000),
            (Task(7, {
                'a': 6,
                'b': (6, 6)
            }, ('this is attachment', 6)), 2985984),
            (Task(8, {
                'a': 7,
                'b': (7, 7)
            }, ('this is attachment', 7)), 105413504),
            (Task(9, {
                'a': 8,
                'b': (8, 8)
            }, ('this is attachment', 8)), 4294967296),
            (Task(10, {
                'a': 9,
                'b': (9, 9)
            }, ('this is attachment', 9)), 198359290368),
        ]

    @pytest.mark.timeout(10)
    def test_base_algorithm_get_session_with_error(self):

        def _my_func(v):
            a, (b0, b1) = v['a'], v['b']
            if a % 3 == 2:
                raise OverflowError('this is overflow', a)

            return (a + b0) ** b1

        _service1 = _TestThreadService(_my_func)
        _session1 = _MyAlgorithm(10).get_session(
            {
                'a': uniform(0, 10),  # these uniform spaces are only placeholders here
                'b': (
                    uniform(0, 10),
                    uniform(0, 10),
                )
            },
            _service1
        )

        try:
            _service1.start()
            _session1.start()
        finally:
            _session1.join()
            _service1.shutdown(wait=True)

        assert _service1.state == ServiceState.DEAD
        assert _service1.error is None
        assert _session1.state == SessionState.DEAD
        assert _session1.error is None

        assert sorted(_session1.reslist) == [
            (Task(1, {
                'a': 0,
                'b': (0, 0)
            }, ('this is attachment', 0)), 1),
            (Task(2, {
                'a': 1,
                'b': (1, 1)
            }, ('this is attachment', 1)), 2),
            (Task(4, {
                'a': 3,
                'b': (3, 3)
            }, ('this is attachment', 3)), 216),
            (Task(5, {
                'a': 4,
                'b': (4, 4)
            }, ('this is attachment', 4)), 4096),
            (Task(7, {
                'a': 6,
                'b': (6, 6)
            }, ('this is attachment', 6)), 2985984),
            (Task(8, {
                'a': 7,
                'b': (7, 7)
            }, ('this is attachment', 7)), 105413504),
            (Task(10, {
                'a': 9,
                'b': (9, 9)
            }, ('this is attachment', 9)), 198359290368),
        ]
        assert sorted(_session1.errlist) == [
            (Task(3, {
                'a': 2,
                'b': (2, 2)
            }, ('this is attachment', 2)), OverflowError, ('this is overflow', 2)),
            (Task(6, {
                'a': 5,
                'b': (5, 5)
            }, ('this is attachment', 5)), OverflowError, ('this is overflow', 5)),
            (Task(9, {
                'a': 8,
                'b': (8, 8)
            }, ('this is attachment', 8)), OverflowError, ('this is overflow', 8)),
        ]

    @pytest.mark.timeout(10)
    def test_base_algorithm_get_session_with_session_error(self):

        def _my_func(v):
            a, (b0, b1) = v['a'], v['b']
            return (a + b0) ** b1

        _service1 = _TestThreadService(_my_func)
        _session1 = _MyAlgorithm(
            10, even_only=True
        ).get_session(
            {
                'a': uniform(0, 10),  # these uniform spaces are only placeholders here
                'b': (
                    uniform(0, 10),
                    uniform(0, 10),
                )
            },
            _service1
        )

        try:
            _service1.start()
            _session1.start()
        finally:
            _session1.join()
            _service1.shutdown(wait=True)

        assert _service1.state == ServiceState.DEAD
        assert _service1.error is None
        assert _session1.state == SessionState.DEAD
        assert _session1.error
        assert isinstance(_session1.error, ValueError)
        assert _session1.error.args == ('Even only, but 1 found.', )

    def test_base_algorithm_start_again(self):

        def _my_func(v):
            a, (b0, b1) = v['a'], v['b']
            return (a + b0) ** b1

        _service1 = _TestThreadService(_my_func)
        _session1 = _MyAlgorithm(10).get_session(
            {
                'a': uniform(0, 10),  # these uniform spaces are only placeholders here
                'b': (
                    uniform(0, 10),
                    uniform(0, 10),
                )
            },
            _service1
        )

        try:
            _service1.start()
            _session1.start()

            with pytest.raises(RuntimeError):
                _session1.start()

        finally:
            _session1.join()
            _service1.shutdown(wait=True)

        assert _service1.state == ServiceState.DEAD
        assert _service1.error is None
        assert _session1.state == SessionState.DEAD
        assert _session1.error is None

    def test_base_algorithm_put_after_dead(self):

        def _my_func(v):
            a, (b0, b1) = v['a'], v['b']
            return (a + b0) ** b1

        _service1 = _TestThreadService(_my_func)
        _session1 = _MyAlgorithm(10).get_session(
            {
                'a': uniform(0, 10),  # these uniform spaces are only placeholders here
                'b': (
                    uniform(0, 10),
                    uniform(0, 10),
                )
            },
            _service1
        )

        try:
            _service1.start()
            _session1.start()
        finally:
            _session1.join()
            _service1.shutdown(wait=True)

        assert _service1.state == ServiceState.DEAD
        assert _service1.error is None
        assert _session1.state == SessionState.DEAD
        assert _session1.error is None

        with pytest.raises(RuntimeError):
            _session1.put({'a': 1, 'b': (2, 3)})
