from operator import __neg__, __pos__

from ..space import BaseSpace


class HyperValue:

    def __init__(self, space: BaseSpace, funcs=None):
        self.__space = space
        self.__funcs = tuple(funcs or ())

    @property
    def space(self) -> BaseSpace:
        return self.__space

    def trans(self, x):
        v = x
        for func in self.__funcs:
            v = func(v)
        return v

    def _then(self, f):
        return self.__class__(self.__space, (*self.__funcs, f))

    def __rshift__(self, other):
        return self._then(other)

    def __add__(self, other):
        return self._then(lambda x: x + other)

    def __radd__(self, other):
        return self._then(lambda x: other + x)

    def __sub__(self, other):
        return self._then(lambda x: x - other)

    def __rsub__(self, other):
        return self._then(lambda x: other - x)

    def __mul__(self, other):
        return self._then(lambda x: x * other)

    def __rmul__(self, other):
        return self._then(lambda x: other * x)

    def __floordiv__(self, other):
        return self._then(lambda x: x // other)

    def __rfloordiv__(self, other):
        return self._then(lambda x: other // x)

    def __truediv__(self, other):
        return self._then(lambda x: x / other)

    def __rtruediv__(self, other):
        return self._then(lambda x: other / x)

    def __mod__(self, other):
        return self._then(lambda x: x % other)

    def __rmod__(self, other):
        return self._then(lambda x: other % x)

    def __pow__(self, other):
        return self._then(lambda x: x ** other)

    def __rpow__(self, other):
        return self._then(lambda x: other ** x)

    def __neg__(self):
        return self._then(__neg__)

    def __pos__(self):
        return self._then(__pos__)
