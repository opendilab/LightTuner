import time
from threading import Thread

import pytest

from ditk.hpo.utils import ValueProxyLock


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
