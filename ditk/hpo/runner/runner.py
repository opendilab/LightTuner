import os
import time
from functools import reduce, wraps
from threading import Lock
from typing import Tuple, Any, Type, Dict, Callable, Optional, Iterator

from hbutils.collection import nested_walk

from .event import RunnerStatus, RunnerEventSet
from .log import LoggingEventSet
from .model import RunSkipped, RunResult, RunFailed, C
from .result import _to_expr, _ResultExpression
from .signal import Skip
from ..algorithm import BaseAlgorithm, OptimizeDirection, Task, BaseSession
from ..utils import ThreadService, Result, EventModel, RankList
from ..value import HyperValue


def _space_exprs(space) -> Iterator[Tuple[str, _ResultExpression]]:
    for path, value in nested_walk(space):
        if isinstance(value, HyperValue):
            name = '.'.join(path)
            expr = reduce(lambda x, y: x[y], path, C)
            yield name, expr


def _expr_to_frank(expr):
    _expr = _to_expr(expr)

    def _func(r: RunResult) -> Any:
        return r.get(_expr)

    return _func


class ParallelSearchRunner:
    def __init__(self, algo_cls: Type[BaseAlgorithm], func, silent: bool = False):
        # about algorithm
        self.__func = func
        try:
            _ = self._settings
        except AttributeError:
            self._settings: Dict[str, object] = {}  # pragma: no cover
        self._settings.update({'max_steps': None, 'opt_direction': None})
        self.__algorithm_cls = algo_cls  # old_algorithm class

        # about control
        self.__max_workers = os.cpu_count()
        self.__max_try = 3
        self.__stop_condition = None

        # about target
        self.__target_key = None
        self.__target_name = 'target'

        # about rank
        self.__rank_capacity = 5
        self.__rank_concerns = []
        self.__spaces = None  # space for searching

        # about logging and events
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

    def max_workers(self, n: int) -> 'ParallelSearchRunner':
        if isinstance(n, int) and n >= 1:
            self.__max_workers = n
            return self
        else:
            raise ValueError(f'Invalid max workers count - {n!r}.')

    def max_retries(self, n: int) -> 'ParallelSearchRunner':
        if isinstance(n, int) and n >= 1:
            self.__max_try = n  # TODO: change n to n+1, this is max_retries
            return self
        else:
            raise ValueError(f'Invalid max retry count - {repr(n)}.')

    def stop_when(self, condition) -> 'ParallelSearchRunner':
        if self.__stop_condition is None:
            self.__stop_condition = _to_expr(condition)
        else:
            self.__stop_condition = self.__stop_condition | _to_expr(condition)

        return self

    def maximize(self, condition, name='target') -> 'ParallelSearchRunner':
        if self._opt_direction is None:
            self._settings['opt_direction'] = 'maximize'
            self.__target_key = _to_expr(condition)
            self.__target_name = name
            return self
        else:
            raise SyntaxError('Maximize or minimize condition should be assigned more than once.')

    def minimize(self, condition, name='target') -> 'ParallelSearchRunner':
        if self._opt_direction is None:
            self._settings['opt_direction'] = 'minimize'
            self.__target_key = _to_expr(condition)
            self.__target_name = name
            return self
        else:
            raise SyntaxError('Maximize or minimize condition should be assigned more than once.')

    def rank(self, n) -> 'ParallelSearchRunner':
        if n >= 1:
            self.__rank_capacity = n
            return self
        else:
            raise ValueError(f'Invalid rank list capacity - {repr(n)}.')

    def concern(self, cond, name):
        self.__rank_concerns.append((name, cond))
        return self

    @property
    def _max_steps(self) -> Optional[int]:
        # noinspection PyTypeChecker
        return self._settings['max_steps']

    @property
    def _opt_direction(self) -> Optional[OptimizeDirection]:
        if self._settings['opt_direction']:
            return OptimizeDirection.loads(self._settings['opt_direction'])
        else:
            return None

    def _is_result_okay(self, retval: RunResult) -> bool:
        return self.__stop_condition and retval.get(self.__stop_condition)

    def spaces(self, vs) -> 'ParallelSearchRunner':
        self.__spaces = vs
        return self

    def _check_config(self):
        if not self._opt_direction:
            raise SyntaxError('Optimize target is not given, '
                              'please use maximize or minimize method to assign a target for optimization.')

    def run(self) -> Optional[Tuple[Any, Any, Any]]:
        self._check_config()
        _events: EventModel = self.__events
        _events.trigger(RunnerStatus.INIT, self.__algorithm_cls, self._settings, self.__func)

        # initialization
        _max_workers = self.__max_workers
        _max_try = self.__max_try

        _target_func = self.__func
        _target_key = self.__target_key
        _params = list(_space_exprs(self.__spaces))

        _rank_lock = Lock()  # ranklist is not thread-safe, protection is necessary
        _rank_concerns = self.__rank_concerns
        _ranklist = RankList(  # put RunResult init
            self.__rank_capacity,
            columns=[
                ('#', lambda x: x.task_id),
                *[(name, _expr_to_frank(expr)) for name, expr in _params],
                (self.__target_name, _expr_to_frank(self.__target_key)),
                *[(name, _expr_to_frank(cond)) for name, cond in _rank_concerns]
            ],
            key=_expr_to_frank(self.__target_key),
            reverse=self._opt_direction == OptimizeDirection.MAXIMIZE,
        )

        _is_cond_meet = False  # if this running is stopped by condition or not
        _error_meet = None  # if any unexpected error is occurred
        _this: ParallelSearchRunner = self

        def _meth_err_wrapper(f):  # wrap the methods in order to show the unexpected errors
            @wraps(f)
            def _new_func(self, *args, **kwargs):
                nonlocal _error_meet
                try:
                    return f(self, *args, **kwargs)
                except BaseException as err:
                    _error_meet = err
                    self.shutdown(False)

            return _new_func

        class AlgorithmRunnerService(ThreadService):
            def __init__(self):
                ThreadService.__init__(self, max_workers=_max_workers)

            def _check_recv(self, task: Task):
                pass  # all task should be approved

            @_meth_err_wrapper
            def _before_exec(self, task: Task):
                _events.trigger(RunnerStatus.STEP, task)

            def _exec(self, task: Task) -> RunResult:
                _task_id, _config, _attachment = task

                r_err, r_metrics = None, None
                for i in range(_max_try):
                    _events.trigger(RunnerStatus.TRY, task, i, _max_try)
                    _before_time = time.time()
                    try:
                        cur_retval, cur_err, cur_skip = _target_func(_config), None, False
                    except Skip as err:
                        cur_retval, cur_err, cur_skip = None, err, True
                    except BaseException as err:
                        cur_retval, cur_err, cur_skip = None, err, False
                    finally:
                        _after_time = time.time()

                    cur_metrics = {'time': _after_time - _before_time}
                    _events.trigger(RunnerStatus.TRY_COMPLETE, task, i, _max_try, cur_metrics)

                    # check the error and result
                    if cur_skip:
                        _events.trigger(RunnerStatus.TRY_SKIP, task, i, _max_try, cur_err.args, cur_metrics)
                        raise RunSkipped(task, cur_err, cur_metrics)
                    elif cur_err is None:
                        _events.trigger(RunnerStatus.TRY_OK, task, i, _max_try, cur_retval, cur_metrics)
                        return RunResult(task, cur_retval, cur_metrics, _target_key)
                    else:
                        _events.trigger(RunnerStatus.TRY_FAIL, task, i, _max_try, cur_err, cur_metrics)
                        r_err, r_metrics = cur_err, cur_metrics

                raise RunFailed(task, r_err, r_metrics)

            @_meth_err_wrapper
            def _after_exec(self, task: Task, result: Result):
                pass  # do nothing here

            @_meth_err_wrapper
            def _after_sentback(self, task: Task, result: Result):

                if result.ok:
                    _events.trigger(RunnerStatus.STEP_OK, task, result.retval)
                    with _rank_lock:
                        retval: RunResult = result.retval
                        _ranklist.append(retval)

                else:
                    error = result.error
                    if isinstance(error, RunFailed):
                        _events.trigger(RunnerStatus.STEP_FAIL, task, result.error)
                    elif isinstance(error, RunSkipped):
                        _events.trigger(RunnerStatus.STEP_SKIP, task, result.error)
                    else:
                        raise RuntimeError('Unexpected error occurred, please notify the developers.')

                _events.trigger(RunnerStatus.STEP_FINAL, task, _ranklist)

            @_meth_err_wrapper
            def _after_callback(self, task: Task, result: Result):
                nonlocal _is_cond_meet
                if result.ok and _this._is_result_okay(result.retval):
                    _is_cond_meet = True
                    self.shutdown(False)

        service = AlgorithmRunnerService()
        algorithm = self.__algorithm_cls(**self._settings)
        session: BaseSession = algorithm.get_session(self.__spaces, service)
        _events.trigger(RunnerStatus.INIT_OK, self.__target_name, _params, _rank_concerns)

        try:
            service.start()
            session.start()
            _events.trigger(RunnerStatus.RUN_START)
        finally:
            session.join()
            service.shutdown(True)

        if _error_meet:
            raise _error_meet
        elif session.error:
            raise session.error
        else:
            _events.trigger(RunnerStatus.RUN_COMPLETE, _is_cond_meet)
            if len(_ranklist) > 0:
                _first: RunResult = _ranklist[0]
                return _first.config, _first.retval, _first.metrics
            else:
                return None
