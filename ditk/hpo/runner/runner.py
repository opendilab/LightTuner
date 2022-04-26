import time
from itertools import islice
from operator import __gt__, __lt__
from typing import Callable, Type, Optional, Tuple, Dict, Any

from .result import R as _OR
from .result import _to_model
from ..algorithm import BaseAlgorithm
from ..utils import ValueProxyLock

R = _OR['return']
M = _OR['metrics']


class SearchRunner:
    def __init__(self, algo_cls: Type[BaseAlgorithm], func):
        self.__func = func
        self.__config: Dict[str, object] = {
            'max_steps': None,
            'opt_direction': None,
        }
        self.__algorithm_cls = algo_cls
        self.__end_condition = None
        self.__order_condition = None
        self.__spaces = None

    def __getattr__(self, item) -> Callable[[object, ], 'SearchRunner']:
        def _get_config_value(v) -> SearchRunner:
            self.__config[item] = v
            return self

        return _get_config_value

    def max_steps(self, n: int) -> 'SearchRunner':
        self.__config['max_steps'] = n
        return self

    def stop_when(self, end_condition) -> 'SearchRunner':
        if self.__end_condition is None:
            self.__end_condition = _to_model(end_condition)
        else:
            self.__end_condition = self.__end_condition | _to_model(end_condition)

        return self

    def maximize(self, condition):
        if self.__order_condition is None:
            self.__order_condition = (_to_model(condition), __gt__)
            self.__config['opt_direction'] = 'maximize'
            return self
        else:
            raise SyntaxError('Maximize or minimize condition should be assigned more than once.')

    def minimize(self, condition):
        if self.__order_condition is None:
            self.__order_condition = (_to_model(condition), __lt__)
            self.__config['opt_direction'] = 'minimize'
            return self
        else:
            raise SyntaxError('Maximize or minimize condition should be assigned more than once.')

    @property
    def _max_steps(self) -> Optional[int]:
        # noinspection PyTypeChecker
        return self.__config['max_steps']

    def _is_result_okay(self, retval):
        if self.__end_condition is not None:
            return not not self.__end_condition(retval)
        else:
            return False

    def spaces(self, vs) -> 'SearchRunner':
        self.__spaces = vs
        return self

    def _is_result_greater(self, origin, newres):
        if self.__order_condition is not None:
            cond, cmp = self.__order_condition
            return cmp(cond(newres), cond(origin))
        else:
            return True

    def _get_result_value(self, res):
        if self.__order_condition is not None:
            conf, _ = self.__order_condition
            return conf(res)
        else:
            return R(res)

    def run(self) -> Optional[Tuple[Any, Any, Any]]:
        proxy_lock = ValueProxyLock()
        iter_obj = self.__algorithm_cls(**self.__config).iter_config(self.__spaces, proxy_lock)
        if self._max_steps is not None:
            iter_obj = islice(iter_obj, self._max_steps)

        current_result = None
        for cfg in iter_obj:
            _before_time = time.time()
            retval = self.__func(cfg)
            _after_time = time.time()
            _duration = _after_time - _before_time

            metrics = {
                'time': _duration,
            }
            fval = {'return': retval, 'metrics': metrics}

            proxy_lock.put(self._get_result_value(fval))
            if current_result is None or self._is_result_greater(current_result[1], fval):
                current_result = (cfg, fval)

            if self._is_result_okay(fval):
                break

        if current_result is not None:
            _cfg, _fval = current_result
            _return, _metrics = _fval['return'], _fval['metrics']
            return _cfg, _return, _metrics  # max step is reached
        else:
            return None
