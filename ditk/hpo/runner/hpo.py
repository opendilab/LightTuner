from typing import Type

from .old_runner import SearchRunner
from ..old_algorithm import BaseAlgorithm, GridSearchAlgorithm, RandomSearchAlgorithm, BayesSearchAlgorithm, \
    RandomConfigure, GridConfigure, BayesConfigure


class _RandomRunner(SearchRunner, RandomConfigure):
    def __init__(self, func, silent: bool = False):
        RandomConfigure.__init__(self, {})
        SearchRunner.__init__(self, RandomSearchAlgorithm, func, silent)


class _GridRunner(SearchRunner, GridConfigure):
    def __init__(self, func, silent: bool = False):
        GridConfigure.__init__(self, {})
        SearchRunner.__init__(self, GridSearchAlgorithm, func, silent)


class _BayesRunner(SearchRunner, BayesConfigure):
    def __init__(self, func, silent: bool = False):
        BayesConfigure.__init__(self, {})
        SearchRunner.__init__(self, BayesSearchAlgorithm, func, silent)


class HpoFunc:
    def __init__(self, func):
        self.__func = func

    def __call__(self, *args, **kwargs):
        return self.__func(*args, **kwargs)

    def search(self, algo_cls: Type[BaseAlgorithm], silent: bool = False) -> SearchRunner:
        return SearchRunner(algo_cls, self.__func, silent)

    def random(self, silent: bool = False) -> _RandomRunner:
        return _RandomRunner(self.__func, silent)

    def grid(self, silent: bool = False) -> _GridRunner:
        return _GridRunner(self.__func, silent)

    def bayes(self, silent: bool = False) -> _BayesRunner:
        return _BayesRunner(self.__func, silent)

    def __repr__(self):
        return f'<{type(self).__name__} of {repr(self.__func)}>'


def hpo(func) -> HpoFunc:
    if isinstance(func, HpoFunc):
        return func
    else:
        return HpoFunc(func)
