from typing import Any, Mapping

from .result import R as _OR
from .result import _to_callable
from .signal import Skip
from ..algorithm import Task

C = _OR['config']
R = _OR['return']
M = _OR['metrics']


class _IResultMetrics:
    def __init__(self, task: Task, metrics: Mapping):
        self.__task = task
        self.__metrics = dict(metrics)

    @property
    def task_id(self) -> int:
        return self.__task.task_id

    @property
    def config(self):
        return self.__task.config

    @property
    def metrics(self) -> dict:
        return self.__metrics


class RunResult(_IResultMetrics):
    def __init__(self, task: Task, retval, metrics: Mapping, rvalue=R):
        _IResultMetrics.__init__(self, task, metrics)
        self.__retval = retval
        self.__rvalue = _to_callable(rvalue)

    @property
    def retval(self) -> Any:
        return self.__retval

    @property
    def _full_value(self):
        return {
            'config': self.config,
            'return': self.__retval,
            'metrics': self.metrics,
        }

    @property
    def value(self):
        return self.__rvalue(self._full_value)

    def get(self, r):
        return _to_callable(r)(self._full_value)

    def __repr__(self):
        return f'<{type(self).__name__} value: {self.value!r}>'


class RunFailed(Exception, _IResultMetrics):
    def __init__(self, task: Task, err: BaseException, metrics: Mapping):
        _IResultMetrics.__init__(self, task, metrics)
        Exception.__init__(self, type(err), *err.args)
        self.__error = err

    @property
    def error(self):
        return self.__error


class RunSkipped(Exception, _IResultMetrics):
    def __init__(self, task: Task, err: Skip, metrics: Mapping):
        _IResultMetrics.__init__(self, task, metrics)
        Exception.__init__(self, *err.args)
        self.with_traceback(err.__traceback__)
