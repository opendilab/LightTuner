from itertools import islice
from operator import __gt__, __lt__
from typing import Callable, Type, Optional, Tuple

from .base import BaseAlgorithm
from .result import _to_model


class SearchRunner:
    def __init__(self, algo_cls: Type[BaseAlgorithm], func):
        self.__func = func
        self.__config = {
            'max_steps': None,
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
            return self
        else:
            raise SyntaxError('Maximize or minimize condition should be assigned more than once.')

    def minimize(self, condition):
        if self.__order_condition is None:
            self.__order_condition = (_to_model(condition), __lt__)
            return self
        else:
            raise SyntaxError('Maximize or minimize condition should be assigned more than once.')

    @property
    def _max_steps(self) -> Optional[int]:
        return self.__config['max_steps']

    def _iter_config(self):
        return self.__algorithm_cls(**self.__config).iter_config(self.__spaces)

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

    def run(self) -> Optional[Tuple[object, object]]:
        iter_obj = enumerate(self._iter_config(), start=1)
        if self._max_steps is not None:
            iter_obj = islice(iter_obj, self._max_steps)

        current_result = None
        for step, cfg in iter_obj:
            retval = self.__func(cfg)
            if current_result is None or self._is_result_greater(current_result[1], retval):
                current_result = (cfg, retval)

            if self._is_result_okay(retval):
                break

        return current_result  # max step is reached
