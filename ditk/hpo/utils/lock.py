from threading import Lock
from typing import Any, Tuple


class RunFailed(Exception):
    pass


class ValueProxyLock:
    def __init__(self):
        self.__rlock = Lock()
        self.__wlock = Lock()
        self.__rlock.acquire()
        self.__value = None

    def put(self, v):
        self.__wlock.acquire()
        self.__value = (True, v)
        self.__rlock.release()

    def fail(self, err):
        self.__wlock.acquire()
        self.__value = (False, err)
        self.__rlock.release()

    def get(self):
        self.__rlock.acquire()
        (success, obj), self.__value = self.__value, None
        self.__wlock.release()
        if success:
            return obj
        else:
            raise RunFailed(obj)


class _CallEnd:
    def end(self):
        raise NotImplementedError  # pragma: no cover

    def __call__(self, v):
        raise NotImplementedError  # pragma: no cover


class _ExecuteEnd:
    def __iter__(self):
        raise NotImplementedError  # pragma: no cover

    def put(self, retval: Any):
        raise NotImplementedError  # pragma: no cover

    def fail(self, err: Exception):
        raise NotImplementedError  # pragma: no cover


def func_interact() -> Tuple[_CallEnd, _ExecuteEnd]:
    _send = ValueProxyLock()
    _get = ValueProxyLock()

    class _FuncCallEnd(_CallEnd):
        def end(self):
            _send.fail(StopIteration)

        def __call__(self, v):
            _send.put(v)
            try:
                return _get.get()
            except RunFailed as err:
                raise err.args[0]

    class _FuncExecuteEnd(_ExecuteEnd):
        def __iter__(self):
            while True:
                try:
                    yield _send.get()
                except RunFailed:
                    break

        def put(self, retval: Any):
            _get.put(retval)

        def fail(self, err: Exception):
            _get.fail(err)

    return _FuncCallEnd(), _FuncExecuteEnd()
