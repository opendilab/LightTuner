import math
import warnings
from queue import Queue, Empty
from typing import Dict, Tuple
from typing import Iterator, Callable, Optional

import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern

from .utils import acq_max, UtilityFunction, ensure_rng
from ..base import BaseOptimizeAlgorithm, OptimizeDirection, AlgorithmConfigure
from ...space import ContinuousSpace, SeparateSpace, FixedSpace
from ...utils import ValueProxyLock, RunFailed
from ...value import HyperValue


def hyper_to_bound(hv: HyperValue) -> Tuple[Tuple[float, float], Callable]:
    space = hv.space
    if isinstance(space, ContinuousSpace):
        return (space.lbound, space.ubound), hv.trans
    elif isinstance(space, SeparateSpace):
        n = space.count
        _start, _step = space.start, space.step

        def _trans(x):
            rx = int(min(math.floor(x), n - 1))
            ax = _start + rx * _step
            return hv.trans(ax)

        return (0.0, float(n)), _trans
    elif isinstance(space, FixedSpace):
        raise TypeError(f'Fixed space is not supported in bayesian optimization, but {hv!r} found.')
    else:
        raise TypeError(f'Unknown space type - {space!r}.')  # pragma: no cover


class BayesConfigure(AlgorithmConfigure):
    def seed(self, s: Optional[int] = None):
        self._settings['seed'] = s
        return self

    def init_steps(self, steps: int):
        self._settings['init_steps'] = steps
        return self

    def set_utils(self, acq=..., kappa=..., kappa_decay=..., kappa_decay_delay=..., xi=...):
        new_values = {
            key: value for key, value in
            dict(acq=acq, kappa=kappa, kappa_decay=kappa_decay,
                 kappa_decay_delay=kappa_decay_delay, xi=xi)
            if value is not Ellipsis
        }
        self._settings.update(new_values)
        return self

    def set_gp_params(self, **gp_params):
        gps = self._settings.get('gp_params', None) or {}
        gps.update(gp_params)
        self._settings['gp_params'] = gps
        return self


class BayesSearchAlgorithm(BaseOptimizeAlgorithm):
    # noinspection PyUnusedLocal
    def __init__(self, opt_direction: OptimizeDirection, seed: Optional[int] = None,
                 max_steps: int = 25, init_steps: int = 5,
                 acq='ucb', kappa=2.576, kappa_decay=1, kappa_decay_delay=0, xi=0.0,
                 gp_params: Optional[Dict] = None, **kwargs):
        BaseOptimizeAlgorithm.__init__(self, opt_direction, **kwargs)
        self._random_seed = seed
        self._max_steps = max_steps
        self._init_steps = init_steps
        self._util_args = (acq, kappa, kappa_decay, kappa_decay_delay, xi)
        self._gp_params = dict(gp_params or {})

    def _process_raw_result(self, v):
        if self.opt_direction == OptimizeDirection.MAXIMIZE:
            return v
        elif self.opt_direction == OptimizeDirection.MINIMIZE:
            return -v
        else:
            assert False, f'Unknown optimization direction - {self.opt_direction!r}.'  # pragma: no cover

    def _iter_spaces(self, vsp: Tuple[HyperValue, ...], pres: ValueProxyLock) -> Iterator[Tuple[object, ...]]:
        pbounds = []
        pfuncs = []
        for hv in vsp:
            (l, r), post = hyper_to_bound(hv)
            pbounds.append((l, r))
            pfuncs.append(post)

        ################################
        # Processing
        ################################
        _random = ensure_rng(self._random_seed)

        ################################
        # Initialize of Space
        ################################
        _space_dim = len(pbounds)
        _space_bounds = np.array(pbounds, dtype=np.float64)
        _space_params = np.empty(shape=(0, _space_dim))
        _space_target = np.empty(shape=0)

        def _space_random_sample() -> np.ndarray:
            data = np.empty((1, _space_dim))
            for col, (lower, upper) in enumerate(_space_bounds):
                data.T[col] = _random.uniform(lower, upper, size=1)
            return data.ravel()

        def _space_append(x: np.ndarray, y: float):
            nonlocal _space_params, _space_target
            _space_params = np.concatenate([_space_params, x.reshape(1, -1)])
            _space_target = np.concatenate([_space_target, [y]])

        def _space_fit():
            nonlocal _opt_regressor
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                _opt_regressor.fit(_space_params, _space_target)

        ################################
        # Initialize of Optimization
        ################################
        _opt_x_queue = Queue()
        _opt_regressor = GaussianProcessRegressor(
            kernel=Matern(nu=2.5),
            alpha=1e-6,
            normalize_y=True,
            n_restarts_optimizer=5,
            random_state=_random,
        )
        _opt_regressor.set_params(**self._gp_params)

        # init queue
        init_points = self._init_steps
        if _opt_x_queue.empty() and len(_space_target) == 0:
            init_points = max(init_points, 1)
        for _ in range(init_points):
            _opt_x_queue.put_nowait(_space_random_sample())

        ################################
        # Start Running
        ################################
        acq, kappa, kappa_decay, kappa_decay_delay, xi = self._util_args
        util = UtilityFunction(acq, kappa, xi, kappa_decay, kappa_decay_delay)

        def _suggest() -> np.ndarray:
            return acq_max(
                ac=util.utility,
                gp=_opt_regressor,
                y_max=_space_target.max(),
                bounds=_space_bounds,
                random_state=_random
            )

        iteration = 0
        while not _opt_x_queue.empty() or iteration < self._max_steps:
            try:  # Get from queue
                x_probe = _opt_x_queue.get_nowait()
            except Empty:
                # Get suggestion
                util.update_params()
                if len(_space_target) == 0:
                    x_probe = _space_random_sample()
                else:
                    _space_fit()
                    x_probe = _suggest()
                iteration += 1

            x_actual = [func(xv) for xv, func in zip(x_probe, pfuncs)]
            yield tuple(x_actual)

            try:
                result = self._process_raw_result(pres.get())
            except RunFailed:  # ignore
                pass
            else:  # register and return
                _space_append(x_probe, result)
