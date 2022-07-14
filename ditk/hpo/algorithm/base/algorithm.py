from enum import IntEnum, unique
from threading import Thread, Lock
from typing import Optional, Tuple, Any

import inflection

from .model import Task
from ...utils import ThreadService, Result
from ...value import struct_values, HyperValue


class BaseConfigure:

    def __init__(self, settings: Optional[dict] = None):
        self._settings = dict(settings or {})


class BaseAlgorithm:

    def __init__(self, **kwargs):
        pass

    def get_session(self, space, service: ThreadService):
        raise NotImplementedError  # pragma: no cover

    @classmethod
    def algorithm_name(cls):
        return inflection.underscore(cls.__name__).replace('_', ' ').strip()


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
        self.__error: Optional[BaseException] = None

        self.__max_id = 0
        self.__sfunc, self.__svalues = struct_values(space)

    @property
    def vsp(self) -> Tuple[HyperValue, ...]:
        return self.__svalues

    @property
    def state(self) -> SessionState:
        with self.__state_lock:
            return self.__state

    def __actual_return(self, task: Task, result: Result):
        self._return(task, result)
        if result.ok:
            self._return_on_success(task, result.retval)
        else:
            self._return_on_failed(task, result.error)

    def _return(self, task: Task, result: Result):
        pass

    def _return_on_success(self, task: Task, retval: Any):
        raise NotImplementedError  # pragma: no cover

    def _return_on_failed(self, task: Task, error: Exception):
        pass  # pragma: no cover

    def put(self, config, attachment: Optional[Tuple[Any, ...]] = None, *, timeout: Optional[float] = None):
        with self.__state_lock:
            if self.__state == SessionState.RUNNING:
                self.__max_id += 1
                self.__service.send(Task(self.__max_id, config, attachment), self.__actual_return, timeout=timeout)
            else:
                raise RuntimeError(f'Algorithm session is {self.__state.name}, sample putting is disabled.')

    def _put_via_space(
        self, vp: Tuple[Any, ...], attachment: Optional[Tuple[Any, ...]] = None, *, timeout: Optional[float] = None
    ):
        self.put(self.__sfunc(*vp), attachment, timeout=timeout)

    def _run(self):
        raise NotImplementedError  # pragma: no cover

    def __actual_run(self):
        try:
            self._run()
        except BaseException as err:
            self.__error = err
        finally:
            self.__service.shutdown()
            with self.__state_lock:
                self.__state = SessionState.DEAD

    @property
    def error(self) -> Optional[BaseException]:
        return self.__error

    def start(self):
        with self.__state_lock:
            if self.__state == SessionState.PENDING:  # not started, just start it
                self.__thread.start()
                self.__state = SessionState.RUNNING
            else:
                raise RuntimeError(f'Algorithm session is {self.__state.name}, starting is not available.')

    def join(self):
        self.__thread.join()
