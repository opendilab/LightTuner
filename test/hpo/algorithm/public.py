from typing import Tuple

from lighttuner.hpo import hpo
from lighttuner.hpo.runner.hpo import HpoFunc

EPS = 1e-8


def get_hpo_func() -> Tuple[list, HpoFunc]:
    visited = []

    @hpo
    def opt(v):
        x, y = v['x'], v['y']
        visited.append(v)

        return {'result': x * y, 'sum': x + y}

    return visited, opt
