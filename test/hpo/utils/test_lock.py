import time
from contextlib import closing
from threading import Thread

import pytest

from ditk.hpo.utils import ValueProxyLock, RunFailed, func_interact


@pytest.mark.unittest
class TestHpoUtilsLock:
    def test_value_proxy_lock(self):
        p = ValueProxyLock()
        result = None

        def _f1():
            nonlocal result
            result = p.get()

        t1 = Thread(target=_f1)
        t1.start()

        time.sleep(0.2)
        assert result is None

        time.sleep(0.1)
        p.put(233)
        t1.join()
        assert result == 233

    def test_value_proxy_lock_fail(self):
        p = ValueProxyLock()
        result = None

        def _f1():
            nonlocal result
            try:
                p.get()
            except Exception as err:
                result = err

        t1 = Thread(target=_f1)
        t1.start()

        time.sleep(0.2)
        assert result is None

        time.sleep(0.1)
        p.fail(ValueError('233', 233))
        t1.join()
        assert isinstance(result, RunFailed)
        assert len(result.args) == 1
        err = result.args[0]
        assert isinstance(err, ValueError)
        assert err.args == ('233', 233)

    def test_func_interact(self):
        _call, _execute = func_interact()
        _vs = [2, 3, 5, 7, -1]
        _vr = []

        def _thread_func():
            with closing(_call):
                for item in _vs:
                    try:
                        _result = _call(item)
                    except ValueError as err:
                        _vr.append((False, err.args[0]))
                    else:
                        _vr.append((True, _result))

        t = Thread(target=_thread_func)
        t.start()

        for v in _execute:
            if v < 2:
                _execute.fail(ValueError(v))
            else:
                _execute.put(v ** 2 + 5)

        t.join()
        assert _vr == [
            (True, 9),
            (True, 14),
            (True, 30),
            (True, 54),
            (False, -1)
        ]

        with pytest.raises(BrokenPipeError):
            _call(233)
