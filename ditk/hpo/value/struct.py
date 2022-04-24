from itertools import chain
from operator import itemgetter
from typing import Tuple, Callable

from .value import HyperValue


def _raw_struct_values(vs):
    if isinstance(vs, dict):
        vkeys, vvalues = [], []
        for key, value in sorted(vs.items()):
            vkeys.append(key)
            vvalues.append(_raw_struct_values(value))


        type_ = type(vs)

        def _process_dict(*x):
            offset, result = 0, {}
            for i, (_pfunc, _pitems, _pcnt) in enumerate(vvalues):
                result[vkeys[i]] = _pfunc(*x[offset:offset + _pcnt])
                offset += _pcnt

            return type_(result)

        return _process_dict, chain(*map(itemgetter(1), vvalues)), sum(map(itemgetter(2), vvalues))
    elif isinstance(vs, (list, tuple)):
        vitems = [_raw_struct_values(item) for item in vs]
        type_ = type(vs)

        def _process_lst(*x):
            offset, result = 0, []
            for _pfunc, _pitems, _pcnt in vitems:
                result.append(_pfunc(*x[offset:offset + _pcnt]))
                offset += _pcnt

            return type_(result)

        return _process_lst, chain(*map(itemgetter(1), vitems)), sum(map(itemgetter(2), vitems))
    elif isinstance(vs, HyperValue):
        return (lambda x: x), iter([vs]), 1
    else:
        return (lambda: vs), iter([]), 0


def struct_values(vs) -> Tuple[Callable, Tuple[HyperValue, ...]]:
    func, iitems, _ = _raw_struct_values(vs)
    return func, tuple(iitems)
