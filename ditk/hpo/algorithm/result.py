from functools import wraps
from operator import eq, lt, le, ne, gt, ge, getitem

from ..utils import is_function


def _to_model(v):
    if isinstance(v, ResultCheckModel):
        return v
    elif is_function(v):
        return ResultCheckModel(v)
    else:
        return ResultCheckModel(lambda x: v)


def _funclize(func):
    @wraps(func)
    def _new_func(*args, **kwargs):
        _args = [_to_model(item) for item in args]
        _kwargs = {key: _to_model(value) for key, value in kwargs.items()}

        def _actual_func(x):
            _vargs = [item(x) for item in _args]
            _vkwargs = {key: value(x) for key, value in _kwargs.items()}
            return func(*_vargs, **_vkwargs)

        return _actual_func

    return _new_func


class ResultCheckModel:
    def __init__(self, func):
        self._func = func

    def __call__(self, x):
        return self._func(x)

    @classmethod
    def _method(cls, mth, *args, **kwargs) -> 'ResultCheckModel':
        return ResultCheckModel(_funclize(mth)(*args, **kwargs))

    def __getitem__(self, item) -> 'ResultCheckModel':
        return self._method(getitem, self, item)

    def __getattr__(self, item) -> 'ResultCheckModel':
        return self._method(getattr, self, item)

    def is_(self, obj):
        return self._method(lambda x, y: x is y, self, obj)

    def abs(self):
        return self._method(abs, self)

    def len(self):
        return self._method(len, self)

    def isinstance_(self, type_):
        return self._method(isinstance, self, type_)

    def __eq__(self, other):
        return self._method(eq, self, other)

    def __ne__(self, other):
        return self._method(ne, self, other)

    def __lt__(self, other):
        return self._method(lt, self, other)

    def __le__(self, other):
        return self._method(le, self, other)

    def __gt__(self, other):
        return self._method(gt, self, other)

    def __ge__(self, other):
        return self._method(ge, self, other)

    def __or__(self, other):
        return self._method(lambda x, y: x or y, self, other)

    def __ror__(self, other):
        return self._method(lambda x, y: y or x, self, other)

    def __and__(self, other):
        return self._method(lambda x, y: x and y, self, other)

    def __rand__(self, other):
        return self._method(lambda x, y: y and x, self, other)

    def __invert__(self):
        return self._method(lambda x: not x, self)


R = ResultCheckModel(lambda x: x)
