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
        self._max_workers = max_workers or os.cpu_count()
        self._exec_pool: Optional[ThreadPoolExecutor] = None
        self._callback_pool: Optional[ThreadPoolExecutor] = None
        self._event_pool: Optional[ThreadPoolExecutor] = None

        self._state = ServiceState.PENDING
        self._state_lock = Lock()
        self._running_count: Optional[int] = None
        self._close_thread: Optional[Thread] = None
        self._close_event = Event()

        self._error_lock = Lock()
        self._error: Optional[BaseException] = None

    @property
    def state(self) -> ServiceState:
        return self._state

    @property
    def error(self) -> Optional[BaseException]:
        with self._error_lock:
            return self._error

    def _shutdown_due_to_error(self, err: BaseException):
        with self._error_lock:
            if self._error is None:
                self._error = err
                self.shutdown(wait=False)

    def _error_wrap(self, method):
        @wraps(method)
        def _new_method(*args, **kwargs):
            try:
                return method(*args, **kwargs)
            except BaseException as err:
                self._shutdown_due_to_error(err)
                raise err

        return _new_method

    def start(self):
        with self._state_lock:
            if self._state == ServiceState.PENDING:
                self._exec_pool = ThreadPoolExecutor(max_workers=self._max_workers)
                self._callback_pool = ThreadPoolExecutor()
                self._event_pool = ThreadPoolExecutor()
                self._state = ServiceState.RUNNING
                self._running_count = 0

    def __check_recv_busy(self):
        if self._running_count >= self._max_workers:
            raise ServiceBusy(f'{plural_word(self._running_count, "running task")}, '
                              f'max workers limits ({self._max_workers}) has already exceeded.')

    @abstractmethod
    def _check_recv(self, task: _TaskType):
        raise NotImplementedError  # pragma: no cover

    def send(self, task: _TaskType, fn_callback: Optional[_TaskCallBackType] = None,
             *, timeout: Optional[float] = None):
        _busy_err = None
        _call_time, _is_tried, _is_sent = time.time(), False, False
        while not _is_tried or timeout is None or _call_time + timeout > time.time():
            _is_tried = True
            _is_busy = False
            with self._state_lock:
                if self._state == ServiceState.PENDING:
                    raise RuntimeError(f'Service is {self._state.name.lower()}.')
                elif self._state == ServiceState.RUNNING:
                    try:
                        self.__check_recv_busy()
                        self._check_recv(task)
                    except ServiceBusy as err:
                        _is_busy, _busy_err = True, err
                    else:
                        self._running_count += 1
                        self._exec_pool.submit(self._error_wrap(self.__actual_exec), task, fn_callback)
                        _is_sent = True
                        break
                else:
                    raise ServiceNoLongerAccept(f'Service is {self._state.name.lower()}, '
                                                f'tasks will be no longer accepted.')

            if _is_busy:  # do not jam the lock, move the sleep out of above
                time.sleep(0.05)

        if not _is_sent and _busy_err is not None:
            raise _busy_err

    def __shutdown(self, already_closing: Event):
        self._state = ServiceState.CLOSING
        already_closing.set()
        self._exec_pool.shutdown(True)
        self._callback_pool.shutdown(True)
        self._event_pool.shutdown(True)
        self._state = ServiceState.DEAD
        self._close_event.set()

    def shutdown(self, wait: bool = False):
        with self._state_lock:
            if self._close_thread is None:
                _already_closing = Event()
                self._close_thread = Thread(target=self.__shutdown, args=(_already_closing,))
                self._close_thread.start()
                _already_closing.wait()

        if wait:
            self._close_thread.join()

    # execution part
    def __actual_exec(self, task: _TaskType, fn_callback: Optional[_TaskCallBackType]):
        try:
            self._before_exec(task)

            try:
                _retval = self._exec(task)
            except BaseException as err:
                _result = Result(False, None, err)
            else:
                _result = Result(True, _retval, None)

            self._after_exec(task, _result)

        finally:
            with self._state_lock:
                self._running_count -= 1

        @wraps(fn_callback)
        def _actual_callback(*args, **kwargs):
            if fn_callback is not None:
                fn_callback(*args, **kwargs)
            self._event_pool.submit(self._error_wrap(self._after_callback), task, _result)

        self._callback_pool.submit(self._error_wrap(_actual_callback), task, _result)
        self._event_pool.submit(self._error_wrap(self._after_sentback), task, _result)

    @abstractmethod
    def _before_exec(self, task: _TaskType):
        raise NotImplementedError  # pragma: no cover

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
