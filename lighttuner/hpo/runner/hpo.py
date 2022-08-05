from typing import Type

from .runner import ParallelSearchRunner
from ..algorithm import RandomAlgorithm, RandomConfigure, GridConfigure, GridAlgorithm, BaseAlgorithm, \
    BayesConfigure, BayesAlgorithm


class _RandomRunner(ParallelSearchRunner, RandomConfigure):

    def __init__(self, func, silent: bool = False):
        RandomConfigure.__init__(self, {})
        ParallelSearchRunner.__init__(self, RandomAlgorithm, func, silent)


class _GridRunner(ParallelSearchRunner, GridConfigure):

    def __init__(self, func, silent: bool = False):
        GridConfigure.__init__(self, {})
        ParallelSearchRunner.__init__(self, GridAlgorithm, func, silent)


class _BayesRunner(ParallelSearchRunner, BayesConfigure):

    def __init__(self, func, silent: bool = False):
        BayesConfigure.__init__(self, {})
        ParallelSearchRunner.__init__(self, BayesAlgorithm, func, silent)


class HpoFunc:

    def __init__(self, func):
        self.__func = func

    def __call__(self, *args, **kwargs):
        return self.__func(*args, **kwargs)

    def search(self, algo_cls: Type[BaseAlgorithm], silent: bool = False) -> ParallelSearchRunner:
        return ParallelSearchRunner(algo_cls, self.__func, silent)

    def random(self, silent: bool = False) -> _RandomRunner:
        return _RandomRunner(self.__func, silent)

    def grid(self, silent: bool = False) -> _GridRunner:
        return _GridRunner(self.__func, silent)

    def bayes(self, silent: bool = False) -> _BayesRunner:
        return _BayesRunner(self.__func, silent)

    def __repr__(self):
        return f'<{type(self).__name__} of {self.__func!r}>'


def hpo(func) -> HpoFunc:
    if isinstance(func, HpoFunc):
        return func
    else:
        return HpoFunc(func)
