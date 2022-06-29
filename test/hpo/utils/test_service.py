import time
from queue import Queue
from typing import Tuple

import pytest

from ditk.hpo.utils import ThreadService, Result, ServiceNoLongerAccept, ServiceBusy
from ditk.hpo.utils.service import ServiceState, _TaskType


class _JoinableThreadService(ThreadService):
    def _check_recv(self, task: _TaskType):
        raise NotImplementedError

    def _before_exec(self, task: _TaskType):
        raise NotImplementedError

    def _exec(self, task: _TaskType) -> object:
        raise NotImplementedError

    def _after_exec(self, task: _TaskType, result: Result):
        raise NotImplementedError

    def _after_sentback(self, task: _TaskType, result: Result):
        raise NotImplementedError

    def _after_callback(self, task: _TaskType, result: Result):
        raise NotImplementedError

    def join(self):  # only for unittest usage
        with self._state_lock:
            if self._state == ServiceState.PENDING:
                return

        self._close_event.wait()


@pytest.mark.unittest
class TestHpoUtilsService:
    @pytest.mark.timeout(20)
    def test_common(self):
        class MyTask:
            _max_id = 0

            def __init__(self, v):
                MyTask._max_id += 1
                self._id = MyTask._max_id
                self.v = v

            @property
            def id(self) -> int:
                return self._id

        class _LocalThreadService(_JoinableThreadService):
            def _check_recv(self, task):
                pass

            def _before_exec(self, task: MyTask):
                pass

            def _exec(self, task: MyTask) -> object:
                time.sleep(0.2)
                return task.v * task.id

            def _after_exec(self, task, result: Result):
                pass

            def _after_sentback(self, task, result: Result):
                pass

            def _after_callback(self, task, result: Result):
                pass

        s = _LocalThreadService(12)
        _res = {}

        def _append_res(task, result: Result):
            nonlocal _res
            _res[task.id] = result.retval

        # stage 0: not started test
        assert s.state == ServiceState.PENDING
        with pytest.raises(RuntimeError):
            s.send(MyTask(233))

        # stage 1: simple test
        s.start()
        assert s.state == ServiceState.RUNNING
        for i in range(12):
            s.send(MyTask((i + 2) ** 2 + 3), _append_res)

        time.sleep(0.5)
        assert _res == {
            2: 14, 3: 36, 4: 76, 5: 140, 6: 234, 7: 364,
            8: 536, 9: 756, 10: 1030, 11: 1364, 12: 1764, 13: 2236,
        }

        # stage 2: waiting test
        _res.clear()
        for i in range(23):
            s.send(MyTask((i + 2) ** 2 + 3), _append_res)

        time.sleep(1.0)
        assert _res == {
            18: 702, 22: 2266, 25: 4300, 21: 1764, 20: 1340, 16: 304,
            14: 98, 17: 476, 15: 180, 23: 2852, 19: 988, 24: 3528,
            27: 6156, 30: 9810, 29: 8468, 28: 7252, 26: 5174, 31: 11284,
            32: 12896, 33: 14652, 34: 16558, 35: 18620, 36: 20844
        }

        for i in range(48):
            s.send(MyTask((i + 2) ** 2 + 3), _append_res)

        assert s.state == ServiceState.RUNNING
        s.shutdown()
        assert s.state == ServiceState.CLOSING
        with pytest.raises(ServiceNoLongerAccept):
            s.send(MyTask(233), _append_res)

        s.shutdown(True)
        assert s.state == ServiceState.DEAD
        assert s.error is None

    @pytest.mark.timeout(20)
    def test_busy_and_error(self):
        class _LocalThreadService(_JoinableThreadService):
            def _check_recv(self, task):
                pass

            def _before_exec(self, task: int):
                pass

            def _exec(self, task: int) -> object:
                time.sleep(1.0)
                if task < 0:
                    raise ValueError(task)
                else:
                    return (task + 1) ** 2 + 3

            def _after_exec(self, task, result: Result):
                pass

            def _after_sentback(self, task, result: Result):
                pass

            def _after_callback(self, task, result: Result):
                pass

        _res_queue = Queue()

        def _put_result(task: id, result: Result):
            _res_queue.put((task, result))

        def _get_result() -> Tuple[int, Result]:
            return _res_queue.get()

        s = _LocalThreadService(1)
        assert s.state == ServiceState.PENDING

        s.start()
        assert s.state == ServiceState.RUNNING

        s.send(1, _put_result)
        with pytest.raises(ServiceBusy):
            s.send(2, _put_result, timeout=0.0)
        _id, _result = _get_result()
        assert _id == 1
        assert _result == Result(True, 7, None)

        s.send(-5, _put_result)
        _id, _result = _get_result()
        assert _id == -5
        assert _result.ok is False
        assert _result.retval is None
        assert isinstance(_result.error, ValueError)
        assert _result.error.args == (-5,)

        assert s.state == ServiceState.RUNNING
        s.shutdown()
        assert s.state in {ServiceState.CLOSING, ServiceState.DEAD}
        s.shutdown(True)
        assert s.state == ServiceState.DEAD
        assert s.error is None

    def test_service_with_error(self):
        class _LocalThreadService(_JoinableThreadService):
            def _check_recv(self, task):
                pass

            def _before_exec(self, task: int):
                if task == 1:
                    raise ValueError(123, '456')

            def _exec(self, task: int) -> object:
                time.sleep(1.0)
                if task < 0:
                    raise ValueError(task)
                else:
                    return (task + 1) ** 2 + 3

            def _after_exec(self, task, result: Result):
                if task == 2:
                    raise KeyError(f'after_exec task: {task}')

            def _after_sentback(self, task, result: Result):
                if task == 3:
                    raise KeyError(f'after_sentback task: {task}')

            def _after_callback(self, task, result: Result):
                if task == 4:
                    raise RuntimeError(f'after_callback task: {task}')

        _res_queue = Queue()

        def _put_result(task: id, result: Result):
            if task == 5:
                raise OverflowError(f'fn_callback task: {task}')
            else:
                _res_queue.put((task, result))

        def _get_result() -> Tuple[int, Result]:
            return _res_queue.get()

        s1 = _LocalThreadService(1)  # error in _before_exec
        assert s1.state == ServiceState.PENDING
        s1.start()
        assert s1.state == ServiceState.RUNNING
        s1.send(1, _put_result)
        s1.join()
        assert s1.state == ServiceState.DEAD
        assert s1.error
        assert isinstance(s1.error, ValueError)
        assert s1.error.args == (123, '456')
        assert _res_queue.empty()

        s2 = _LocalThreadService(1)  # error in _after_exec
        assert s2.state == ServiceState.PENDING
        s2.start()
        assert s2.state == ServiceState.RUNNING
        s2.send(2, _put_result)
        s2.join()
        assert s2.state == ServiceState.DEAD
        assert s2.error
        assert isinstance(s2.error, KeyError)
        assert s2.error.args == ('after_exec task: 2',)
        assert _res_queue.empty()

        s3 = _LocalThreadService(1)  # error in _after_sentback
        assert s3.state == ServiceState.PENDING
        s3.start()
        assert s3.state == ServiceState.RUNNING
        s3.send(3, _put_result)
        s3.join()
        assert s3.state == ServiceState.DEAD
        assert s3.error
        assert isinstance(s3.error, KeyError)
        assert s3.error.args == ('after_sentback task: 3',)
        assert not _res_queue.empty()
        assert _get_result() == (3, Result(True, 19, None))

        s4 = _LocalThreadService(1)  # error in _after_callback
        assert s4.state == ServiceState.PENDING
        s4.start()
        assert s4.state == ServiceState.RUNNING
        s4.send(4, _put_result)
        s4.join()
        assert s4.state == ServiceState.DEAD
        assert s4.error
        assert isinstance(s4.error, RuntimeError)
        assert s4.error.args == ('after_callback task: 4',)
        assert not _res_queue.empty()
        assert _get_result() == (4, Result(True, 28, None))

        s5 = _LocalThreadService(1)  # error in fn_callback
        assert s5.state == ServiceState.PENDING
        s5.start()
        assert s5.state == ServiceState.RUNNING
        s5.send(5, _put_result)
        s5.join()
        assert s5.state == ServiceState.DEAD
        assert s5.error
        assert isinstance(s5.error, OverflowError)
        assert s5.error.args == ('fn_callback task: 5',)
        assert _res_queue.empty()
