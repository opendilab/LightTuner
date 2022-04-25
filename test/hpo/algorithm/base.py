from typing import Tuple

from ditk.hpo import hpo
from ditk.hpo.algorithm.hpo import HpoFunc

EPS = 1e-8


def get_hpo_func() -> Tuple[list, HpoFunc]:
    visited = []

    @hpo
    def opt(v):
        x, y = v['x'], v['y']
        visited.append(v)

        return {'result': x * y, 'sum': x + y}

    return visited, opt
