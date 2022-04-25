from typing import Type

from .base import BaseAlgorithm
from .grid import GridAlgorithm
from .random import RandomAlgorithm
from .runner import SearchRunner


class HpoFunc:
    def __init__(self, func):
        self.__func = func

    def __call__(self, *args, **kwargs):
        return self.__func(*args, **kwargs)

    def _search(self, algo_cls: Type[BaseAlgorithm]) -> SearchRunner:
        return SearchRunner(algo_cls, self.__func)

    def random(self) -> 'SearchRunner':
        return self._search(RandomAlgorithm)

    def grid(self) -> 'SearchRunner':
        return self._search(GridAlgorithm)

    def __repr__(self):
        return f'<{type(self).__name__} of {repr(self.__func)}>'


def hpo(func) -> HpoFunc:
    if isinstance(func, HpoFunc):
        return func
    else:
        return HpoFunc(func)
