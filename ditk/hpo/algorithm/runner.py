from typing import Callable, Type, Optional

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

    def never_stop(self) -> 'SearchRunner':
        self.__end_condition = None
        return self

    @property
    def _max_steps(self) -> Optional[int]:
        return self.__config['max_steps']

    def _iter_config(self):
        return self.__algorithm_cls(**self.__config).iter_config(self.__spaces)

    def _ret_can_end(self, retval):
        if self.__end_condition is not None:
            return not not self.__end_condition(retval)
        else:
            return False

    def spaces(self, vs) -> 'SearchRunner':
        self.__spaces = vs
        return self

    def run(self):
        for step, cfg in enumerate(self._iter_config(), start=1):
            retval = self.__func(cfg)
            if self._max_steps is not None and step >= self._max_steps:
                return  # max step is reached
            if self._ret_can_end(retval):
                return  # condition is meet
