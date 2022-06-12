from typing import Type

from .runner import SearchRunner
from ..algorithm import BaseAlgorithm, GridSearchAlgorithm, RandomSearchAlgorithm, BayesSearchAlgorithm, \
    RandomConfigure, GridConfigure, BayesConfigure


class _RandomRunner(SearchRunner, RandomConfigure):
    def __init__(self, func):
        RandomConfigure.__init__(self, {})
        SearchRunner.__init__(self, RandomSearchAlgorithm, func)


class _GridRunner(SearchRunner, GridConfigure):
    def __init__(self, func):
        GridConfigure.__init__(self, {})
        SearchRunner.__init__(self, GridSearchAlgorithm, func)


class _BayesRunner(SearchRunner, BayesConfigure):
    def __init__(self, func):
        BayesConfigure.__init__(self, {})
        SearchRunner.__init__(self, BayesSearchAlgorithm, func)


class HpoFunc:
    def __init__(self, func):
        self.__func = func

    def __call__(self, *args, **kwargs):
        return self.__func(*args, **kwargs)

    def search(self, algo_cls: Type[BaseAlgorithm]) -> SearchRunner:
        return SearchRunner(algo_cls, self.__func)

    def random(self) -> _RandomRunner:
        return _RandomRunner(self.__func)

    def grid(self) -> _GridRunner:
        return _GridRunner(self.__func)

    def bayes(self) -> _BayesRunner:
        return _BayesRunner(self.__func)

    def __repr__(self):
        return f'<{type(self).__name__} of {repr(self.__func)}>'


def hpo(func) -> HpoFunc:
    if isinstance(func, HpoFunc):
        return func
    else:
        return HpoFunc(func)
