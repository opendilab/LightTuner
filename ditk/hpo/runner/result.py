import statistics
from typing import Callable, Any

from hbutils.expression import GeneralExpression, efunc, raw

from ..utils import is_function


class _ResultExpression(GeneralExpression):
    def is_(self, obj):
        return self._func(lambda x, y: x is y, self, obj)

    def len(self):
        return self._func(len, self)

    def abs(self):
        return self._func(abs, self)

    def isinstance_(self, obj):
        return self._func(isinstance, self, raw(obj) if isinstance(obj, type) else obj)

    def sum(self):
        return self._func(sum, self)

    def mean(self):
        return self._func(lambda x: float(statistics.mean(x)), self)

    def stdev(self):
        return self._func(statistics.stdev, self)


R = _ResultExpression()


def _to_expr(e) -> _ResultExpression:
    if isinstance(e, _ResultExpression):
        return e
    elif is_function(e):
        return _ResultExpression(e)
    else:
        return _ResultExpression(lambda x: e)


def _to_callable(e) -> Callable[[Any, ], Any]:
    return efunc(_to_expr(e))
