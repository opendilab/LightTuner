from enum import IntEnum, unique
from threading import Thread, Lock
from typing import Optional, Tuple, Any

import inflection
from hbutils.model import int_enum_loads

from ..utils import ThreadService, Result
from ..value import struct_values, HyperValue


@int_enum_loads(name_preprocess=str.upper)
@unique
class OptimizeDirection(IntEnum):
    MAXIMIZE = 1
    MINIMIZE = 2


class BaseConfigure:
    def __init__(self, settings: Optional[dict] = None):
        self._settings = dict(settings or {})


class BaseAlgorithm:
    def get_session(self, space, service: ThreadService):
        raise NotImplementedError  # pragma: no cover

    @classmethod
    def algorithm_name(cls):
        return inflection.underscore(cls.__name__).replace('_', ' ')


@unique
class SessionState(IntEnum):
    PENDING = 1
    RUNNING = 2
    DEAD = 3


class BaseSession:
    def __init__(self, space, service: ThreadService):
        self.__service = service
        self.__state = SessionState.PENDING
        self.__state_lock: Lock = Lock()
        self.__thread: Optional[Thread] = Thread(target=self.__actual_run)

        self.__max_id = 0
        self.__sfunc, self.__svalues = struct_values(space)

    def __actual_return(self, task: Tuple[int, Any, Any], result: Result):
        self._return(task, result)
        if result.ok:
            self._return_on_success(task, result.retval)
        else:
            self._return_on_failed(task, result.error)

    def _return(self, task: Tuple[int, Any, Any], result: Result):
        pass

    def _return_on_success(self, task: Tuple[int, Any, Any], retval: Any):
        raise NotImplementedError  # pragma: no cover

    def _return_on_failed(self, task: Tuple[int, Any, Any], error: Exception):
        pass

    def put(self, task: Tuple[Any, Any], *, timeout: Optional[float] = None):
        with self.__state_lock:
            if self.__state == SessionState.RUNNING:
                self.__max_id += 1
                self.__service.send((self.__max_id, *task), self.__actual_return, timeout=timeout)
            else:
                raise RuntimeError(f'Algorithm session is {self.__state.name}, sample putting is disabled.')

    def _put_via_space(self, vp: Tuple[Any, ...], attached: Optional[Tuple[Any, ...]] = None,
                       *, timeout: Optional[float] = None):
        self.put((self.__sfunc(*vp), attached), timeout=timeout)

    def _run(self, vsp: Tuple[HyperValue, ...]):
        raise NotImplementedError  # pragma: no cover

    def __actual_run(self):
        try:
            self._run(self.__svalues)
        finally:
            self.__service.shutdown()
            with self.__state_lock:
                self.__state = SessionState.DEAD

    def start(self):
        with self.__state_lock:
            if self.__state == SessionState.PENDING:
                self.__thread.start()
                self.__state = SessionState.RUNNING
            else:
                raise RuntimeError(f'Algorithm session is {self.__state.name}, starting is not available.')

    def join(self):
        self.__thread.join()
