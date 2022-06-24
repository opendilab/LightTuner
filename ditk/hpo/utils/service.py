import os
import time
from abc import ABCMeta, abstractmethod
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
from enum import IntEnum
from functools import wraps
from threading import Lock, Thread, Event
from typing import Optional, TypeVar, Callable, Any

from hbutils.string import plural_word


class ServiceState(IntEnum):
    PENDING = 1  # not started
    RUNNING = 2  # started and running, new request can be accepted
    CLOSING = 3  # closing, new request will be no longer accepted
    DEAD = 4  # completed died


_TaskType = TypeVar('_TaskType')
Result = namedtuple('Result', ['ok', 'retval', 'error'])
_TaskCallBackType = Callable[[_TaskType, Result], Any]


class ServiceBusy(BaseException):
    pass


class ServiceReject(BaseException):
    pass


class ServiceNoLongerAccept(BaseException):
    pass


class ThreadService(metaclass=ABCMeta):
    def __init__(self, max_workers=None):
        self.__max_workers = max_workers or os.cpu_count()
        self.__exec_pool: Optional[ThreadPoolExecutor] = None
        self.__callback_pool: Optional[ThreadPoolExecutor] = None
        self.__event_pool: Optional[ThreadPoolExecutor] = None

        self.__state = ServiceState.PENDING
        self.__state_lock = Lock()
        self.__running_count: Optional[int] = None
        self.__close_thread: Optional[Thread] = None

    @property
    def state(self) -> ServiceState:
        return self.__state

    def start(self):
        with self.__state_lock:
            if self.__state == ServiceState.PENDING:
                self.__exec_pool = ThreadPoolExecutor(max_workers=self.__max_workers)
                self.__callback_pool = ThreadPoolExecutor()
                self.__event_pool = ThreadPoolExecutor()
                self.__state = ServiceState.RUNNING
                self.__running_count = 0

    def __check_recv_busy(self):
        if self.__running_count >= self.__max_workers:
            raise ServiceBusy(f'{plural_word(self.__running_count, "running task")}, '
                              f'max workers limits ({self.__max_workers}) has already exceeded.')

    @abstractmethod
    def _check_recv(self, task: _TaskType):
        raise NotImplementedError  # pragma: no cover

    def send(self, task: _TaskType, fn_callback: Optional[_TaskCallBackType] = None,
             *, timeout: Optional[float] = None):
        _busy = None
        _call_time, _is_tried, _is_sent = time.time(), False, False
        while not _is_tried or timeout is None or _call_time + timeout > time.time():
            _is_tried = True
            with self.__state_lock:
                if self.__state == ServiceState.PENDING:
                    raise RuntimeError(f'Service is {self.__state.name.lower()}.')
                elif self.__state == ServiceState.RUNNING:
                    try:
                        self.__check_recv_busy()
                        self._check_recv(task)
                    except ServiceBusy as err:
                        _busy = err
                        time.sleep(0.05)
                    else:
                        self.__running_count += 1
                        self.__exec_pool.submit(self.__actual_exec, task, fn_callback)
                        _is_sent = True
                        break
                else:
                    raise ServiceNoLongerAccept(f'Service is {self.__state.name.lower()}, '
                                                f'tasks will be no longer accepted.')

        if not _is_sent and _busy is not None:
            raise _busy

    def __shutdown(self, already_closing: Event):
        self.__state = ServiceState.CLOSING
        already_closing.set()
        self.__exec_pool.shutdown(True)
        self.__callback_pool.shutdown(True)
        self.__event_pool.shutdown(True)
        self.__state = ServiceState.DEAD

    def shutdown(self, wait: bool = False):
        with self.__state_lock:
            if self.__close_thread is None:
                _already_closing = Event()
                self.__close_thread = Thread(target=self.__shutdown, args=(_already_closing,))
                self.__close_thread.start()
                _already_closing.wait()

        if wait:
            self.__close_thread.join()

    # execution part
    def __actual_exec(self, task: _TaskType, fn_callback: Optional[_TaskCallBackType]):
        try:
            try:
                _retval = self._exec(task)
            except BaseException as err:
                _result = Result(False, None, err)
            else:
                _result = Result(True, _retval, None)

        finally:
            with self.__state_lock:
                self.__running_count -= 1

        @wraps(fn_callback)
        def _actual_callback(*args, **kwargs):
            if fn_callback is not None:
                fn_callback(*args, **kwargs)
            self.__event_pool.submit(self._after_callback, task, _result)

        self._after_exec(task, _result)
        self.__callback_pool.submit(_actual_callback, task, _result)
        self.__event_pool.submit(self._after_sentback, task, _result)

    @abstractmethod
    def _exec(self, task: _TaskType) -> object:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def _after_exec(self, task: _TaskType, result: Result):
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def _after_sentback(self, task: _TaskType, result: Result):
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def _after_callback(self, task: _TaskType, result: Result):
        raise NotImplementedError  # pragma: no cover
