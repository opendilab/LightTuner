import time
from typing import Tuple, Any, Mapping, Type, Dict, Callable

from .event import RunnerStatus, RunnerEventSet
from .log import LoggingEventSet
from .result import R as _OR
from .result import _to_callable
from ..algorithm import BaseAlgorithm
from ..utils import ThreadService, Result, EventModel


class SkipSample(BaseException):
    pass


R = _OR['return']
M = _OR['metrics']


class RunResult:
    def __init__(self, return_, metrics, rvalue=R):
        self.__return_ = return_
        self.__metrics: dict = dict(metrics)
        self.__rvalue = _to_callable(rvalue)

    @property
    def return_(self) -> Any:
        return self.__return_

    @property
    def metrics(self) -> dict:
        return self.__metrics

    @property
    def _full_value(self):
        return {
            'return': self.__return_,
            'metrics': self.__metrics,
        }

    @property
    def value(self):
        return self.__rvalue(self._full_value)

    def get(self, r):
        return _to_callable(r)(self._full_value)


class RunFailed(Exception):
    def __init__(self, err: BaseException, metrics: Mapping):
        Exception.__init__(self, err, dict(metrics))

    @property
    def error(self):
        err, _ = self.args
        return err

    @property
    def metrics(self) -> dict:
        _, metrics = self.args
        return metrics


class RunSkipped(Exception):
    def __init__(self, metrics: Mapping):
        Exception.__init__(self, dict(metrics))

    @property
    def metrics(self) -> dict:
        metrics, = self.args
        return metrics


_TaskType = Tuple[int, Any, Any]


class AlgorithmRunnerService(ThreadService):
    def __init__(self, func, target_exp, max_workers=None, max_try=3):
        ThreadService.__init__(self, max_workers=max_workers)
        self.__func = func
        self.__target_exp = target_exp
        self.__max_try = max_try

    def _check_recv(self, task: _TaskType):
        pass  # all task should be approved

    def _before_exec(self, task: _TaskType):
        # shown input config
        # self.__events.trigger(RunnerStatus.STEP, cur_istep, cur_cfg)
        pass

    def _exec(self, task: _TaskType) -> RunResult:
        _task_id, _config, _attachment = task

        r_err, r_metrics = None, None
        for i in range(self.__max_try):
            # run the function once
            # self.__events.trigger(RunnerStatus.TRY, i, self.__max_try)

            _before_time = time.time()
            try:
                cur_retval, cur_err, cur_skip = self.__func(_config), None, False
            except SkipSample as err:
                cur_retval, cur_err, cur_skip = None, err, True
            except BaseException as err:
                cur_retval, cur_err, cur_skip = None, err, False
            finally:
                _after_time = time.time()

            cur_metrics = {'time': _after_time - _before_time}
            # self.__events.trigger(RunnerStatus.TRY_COMPLETE, r_metrics)

            # check the error and result
            if cur_skip:
                # self.__events.trigger(RunnerStatus.TRY_SKIP, cur_err.args)
                raise RunSkipped(cur_metrics)
            elif cur_err is None:
                # self.__events.trigger(RunnerStatus.TRY_OK, retval)
                return RunResult(cur_retval, cur_metrics, self.__target_exp)
            else:
                # self.__events.trigger(RunnerStatus.TRY_FAIL, cur_err)
                r_err, r_metrics = cur_err, cur_metrics

        raise RunFailed(r_err, r_metrics)

    def _after_exec(self, task: _TaskType, result: Result):
        pass  # do nothing here

    def _after_sentback(self, task: _TaskType, result: Result):
        if result.ok:
            # get full data
            # self.__events.trigger(RunnerStatus.STEP_OK, r_retval, metrics)
            pass

        else:
            error = result.error
            if isinstance(error, RunFailed):
                # log the exception
                # self.__events.trigger(RunnerStatus.STEP_FAIL, r_err, metrics)
                pass

            elif isinstance(error, RunSkipped):
                # log the skipped information
                # self.__events.trigger(RunnerStatus.STEP_SKIP, r_err.args, metrics)
                pass

            else:
                raise RuntimeError('Unexpected error occurred, please notify the developers.')

        # print ranklist and running duration
        # self.__events.trigger(RunnerStatus.STEP_FINAL, ranklist)

    def _after_callback(self, task: _TaskType, result: Result):
        pass  # do nothing here


class ParallelSearchRunner:
    def __init__(self, algo_cls: Type[BaseAlgorithm], func, silent: bool = False):
        self.__func = func
        try:
            _ = self._settings
        except AttributeError:
            self._settings: Dict[str, object] = {}  # pragma: no cover
        self._settings.update({'max_steps': None, 'opt_direction': None})

        self.__algorithm_cls = algo_cls  # old_algorithm class
        self.__max_try = 3
        self.__algorithm_cls = algo_cls  # old_algorithm class
        self.__max_try = 3
        self.__stop_condition = None  # end condition, determine when to stop
        self.__order_condition = None  # order condition, determine which is the best
        self.__target_name = 'target'
        self.__rank_capacity = 5  # rank list capacity
        self.__rank_concerns = []
        self.__spaces = None  # space for searching

        self.__events = EventModel(RunnerStatus)
        if not silent:
            self.add_event_set(LoggingEventSet(None))

    def add_event_set(self, e: RunnerEventSet):
        prefix = f'{type(e).__name__}_{hex(id(e))}'
        for _, member in RunnerStatus.__members__.items():
            func_name = member.func_name
            self.__events.bind(member, getattr(e, func_name), f'{prefix}_{func_name}')

    def __getattr__(self, item) -> Callable[[object, ], 'ParallelSearchRunner']:
        def _get_config_value(v) -> ParallelSearchRunner:
            self._settings[item] = v
            return self

        return _get_config_value

    def max_steps(self, n: int) -> 'ParallelSearchRunner':
        self._settings['max_steps'] = n
        return self

    def max_retries(self, n: int) -> 'ParallelSearchRunner':
        if isinstance(n, int) and n >= 1:
            self.__max_try = n  # TODO: change n to n+1, this is max_retries
            return self
        else:
            raise ValueError(f'Invalid max retry count - {repr(n)}.')
