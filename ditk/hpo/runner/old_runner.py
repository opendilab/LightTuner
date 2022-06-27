import time
from itertools import islice
from operator import __gt__, __lt__
from typing import Callable, Type, Optional, Tuple, Dict, Any

from .event import RunnerStatus, RunnerEventSet
from .log import LoggingEventSet
from .result import R as _OR, _to_expr
from .result import _to_callable
from ..old_algorithm import BaseAlgorithm
from ..utils import EventModel, ValueProxyLock


class SkipSample(BaseException):
    pass


R = _OR['return']
M = _OR['metrics']


class SearchRunner:
    def __init__(self, algo_cls: Type[BaseAlgorithm], func, silent: bool = False):
        self.__func = func
        try:
            _ = self._settings
        except AttributeError:
            self._settings: Dict[str, object] = {}  # pragma: no cover
        self._settings.update({'max_steps': None, 'opt_direction': None})

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

    def __getattr__(self, item) -> Callable[[object, ], 'SearchRunner']:
        def _get_config_value(v) -> SearchRunner:
            self._settings[item] = v
            return self

        return _get_config_value

    def max_steps(self, n: int) -> 'SearchRunner':
        self._settings['max_steps'] = n
        return self

    def max_retries(self, n: int) -> 'SearchRunner':
        if isinstance(n, int) and n >= 1:
            self.__max_try = n
            return self
        else:
            raise ValueError(f'Invalid max retry count - {repr(n)}.')

    def stop_when(self, condition) -> 'SearchRunner':
        if self.__stop_condition is None:
            self.__stop_condition = _to_expr(condition)
        else:
            self.__stop_condition = self.__stop_condition | _to_expr(condition)

        return self

    def maximize(self, condition, name='target') -> 'SearchRunner':
        if self.__order_condition is None:
            self.__order_condition = (_to_expr(condition), __gt__)
            self._settings['opt_direction'] = 'maximize'
            self.__target_name = name
            return self
        else:
            raise SyntaxError('Maximize or minimize condition should be assigned more than once.')

    def minimize(self, condition, name='target') -> 'SearchRunner':
        if self.__order_condition is None:
            self.__order_condition = (_to_expr(condition), __lt__)
            self._settings['opt_direction'] = 'minimize'
            self.__target_name = name
            return self
        else:
            raise SyntaxError('Maximize or minimize condition should be assigned more than once.')

    def rank(self, n) -> 'SearchRunner':
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

    def _is_result_okay(self, retval):
        if self.__stop_condition is not None:
            return not not _to_callable(self.__stop_condition)(retval)
        else:
            return False

    def spaces(self, vs) -> 'SearchRunner':
        self.__spaces = vs
        return self

    def _is_result_better(self, origin, newres):
        if self.__order_condition is not None:
            _e_cond, cmp = self.__order_condition
            cond = _to_callable(_e_cond)
            return cmp(cond(newres), cond(origin))
        else:
            return True

    def _get_result_value(self, res):
        if self.__order_condition is not None:
            _e_cond, _ = self.__order_condition
            return _to_callable(_e_cond)(res)
        else:
            return R(res)

    def run(self) -> Optional[Tuple[Any, Any, Any]]:
        # old_algorithm information
        self.__events.trigger(
            RunnerStatus.INIT,
            self.__algorithm_cls,
            self._settings,
            self.__func,
        )

        # initializing old_algorithm
        passback = ValueProxyLock()
        cfg_iter = self.__algorithm_cls(**self._settings).iter_config(self.__spaces, passback)
        if self._max_steps is not None:
            cfg_iter = islice(cfg_iter, self._max_steps)
        self.__events.trigger(
            RunnerStatus.INIT_OK,
            self.__spaces,
            [
                (self.__target_name, self._get_result_value),
                *self.__rank_concerns,
            ]
        )

        # run the search
        ranklist, break_by_stop = [], False
        self.__events.trigger(RunnerStatus.RUN_START)
        for cur_istep, cur_cfg in enumerate(cfg_iter, start=1):
            # shown input config
            self.__events.trigger(RunnerStatus.STEP, cur_istep, cur_cfg)

            # run the function with several tries
            r_retval, r_err, r_skip, r_time_cost = None, None, None, None
            for i in range(self.__max_try):
                # run the function once
                self.__events.trigger(RunnerStatus.TRY, i, self.__max_try)

                _before_time = time.time()
                try:
                    retval, cur_err, need_skip = self.__func(cur_cfg), None, False
                except SkipSample as err:
                    retval, cur_err, need_skip = None, err, True
                except BaseException as err:
                    retval, cur_err, need_skip = None, err, False
                finally:
                    _after_time = time.time()
                r_time_cost = _after_time - _before_time
                r_metrics = {'time': r_time_cost}
                self.__events.trigger(RunnerStatus.TRY_COMPLETE, r_metrics)

                # check the error and result
                if not need_skip:
                    if cur_err is None:
                        self.__events.trigger(RunnerStatus.TRY_OK, retval)
                        r_err, r_retval, r_skip = None, retval, False
                        break
                    else:
                        self.__events.trigger(RunnerStatus.TRY_FAIL, cur_err)
                        r_err, r_skip = cur_err, False
                else:
                    self.__events.trigger(RunnerStatus.TRY_SKIP, cur_err.args)
                    r_err, r_skip = cur_err, True
                    break

            can_break = False
            metrics = {'time': r_time_cost}
            if not r_skip:
                if r_err is None:
                    # get full data
                    full_result = {'return': r_retval, 'metrics': metrics}
                    self.__events.trigger(RunnerStatus.STEP_OK, r_retval, metrics)

                    # maintain the ranklist
                    passback.put(self._get_result_value(full_result))
                    ins_pos = None
                    for i, (_, _, fres) in enumerate(ranklist):
                        if self._is_result_better(fres, full_result):
                            ins_pos = i
                            break
                    if ins_pos is None:
                        ranklist.append((cur_istep, cur_cfg, full_result))
                    else:
                        ranklist = ranklist[:ins_pos] + [(cur_istep, cur_cfg, full_result)] + ranklist[ins_pos:]
                    ranklist = ranklist[:self.__rank_capacity]

                    # condition check
                    if self._is_result_okay(full_result):
                        can_break = True

                else:
                    # log the exception
                    self.__events.trigger(RunnerStatus.STEP_FAIL, r_err, metrics)
                    passback.fail(r_err)

            else:
                # log the skipped information
                self.__events.trigger(RunnerStatus.STEP_SKIP, r_err.args, metrics)
                passback.fail(r_err)

            # print ranklist and running duration
            self.__events.trigger(RunnerStatus.STEP_FINAL, ranklist)

            # condition check
            if can_break:
                break_by_stop = True
                break

        # ending information
        self.__events.trigger(RunnerStatus.RUN_COMPLETE, break_by_stop)

        # return
        if ranklist:
            final_step, final_cfg, final_result = ranklist[0]
            final_return, final_metrics = final_result['return'], final_result['metrics']
            return final_cfg, final_return, final_metrics  # max step is reached
        else:
            return None
