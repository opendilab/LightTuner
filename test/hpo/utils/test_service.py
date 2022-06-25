import time
from queue import Queue
from typing import Tuple

import pytest

from ditk.hpo.utils import ThreadService, Result, ServiceNoLongerAccept, ServiceBusy
from ditk.hpo.utils.service import ServiceState


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

        class _LocalThreadService(ThreadService):
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

    @pytest.mark.timeout(20)
    def test_busy_and_error(self):
        class _LocalThreadService(ThreadService):
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
