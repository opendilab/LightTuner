from typing import Type

from .runner import SearchRunner
from ..algorithm import BaseAlgorithm, GridSearchAlgorithm, RandomSearchAlgorithm, BayesSearchAlgorithm


class HpoFunc:
    def __init__(self, func):
        self.__func = func

    def __call__(self, *args, **kwargs):
        return self.__func(*args, **kwargs)

    def _search(self, algo_cls: Type[BaseAlgorithm]) -> SearchRunner:
        return SearchRunner(algo_cls, self.__func)

    def random(self) -> 'SearchRunner':
        return self._search(RandomSearchAlgorithm)

    def grid(self) -> 'SearchRunner':
        return self._search(GridSearchAlgorithm)

    def bayes(self) -> 'SearchRunner':
        return self._search(BayesSearchAlgorithm)

    def __repr__(self):
        return f'<{type(self).__name__} of {repr(self.__func)}>'


def hpo(func) -> HpoFunc:
    if isinstance(func, HpoFunc):
        return func
    else:
        return HpoFunc(func)
