import warnings
from queue import Queue
from threading import Lock, Event
from typing import Dict, Any, Tuple, Callable, List, Optional

import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern

from .allocation import hyper_to_bound
from .utils import ensure_rng, UtilityFunction, acq_max
from ..base import BaseAlgorithm, OptimizeDirection, BaseConfigure, BaseSession, Task
from ...utils import ThreadService, ServiceNoLongerAccept


class BayesConfigure(BaseConfigure):
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


class BayesAlgorithm(BaseAlgorithm):
    # noinspection PyUnusedLocal
    def __init__(self, opt_direction: OptimizeDirection, seed: Optional[int] = None,
                 max_steps: Optional[int] = None, init_steps: int = 5,
                 acq='ucb', kappa=2.576, kappa_decay=1, kappa_decay_delay=0, xi=0.0,
                 gp_params: Optional[Dict] = None, **kwargs):
        BaseAlgorithm.__init__(self, **kwargs)
        self.opt_direction = OptimizeDirection.loads(opt_direction)
        self.random_seed = seed
        self.max_steps = max_steps
        self.init_steps = init_steps
        self.fit_steps = 1  # fit every time receiving new result
        self.util_args = (acq, kappa, kappa_decay, kappa_decay_delay, xi)
        self.gp_params = dict(gp_params or {})

    def get_session(self, space, service: ThreadService) -> 'BayesSession':
        return BayesSession(self, space, service)


class BayesSession(BaseSession):
    def __init__(self, algorithm: BayesAlgorithm, space, service: ThreadService):
        BaseSession.__init__(self, space, service)
        self.__algorithm: BayesAlgorithm = algorithm

        self._pbounds: List[Tuple[float, float]] = []
        self._pfuncs: List[Callable[[float, ], Any]] = []
        for hv in self.vsp:
            (l, r), post = hyper_to_bound(hv)
            self._pbounds.append((l, r))
            self._pfuncs.append(post)

        self._random = ensure_rng(self.__algorithm.random_seed)
        self._space_dim = len(self._pbounds)
        self._space_bounds = np.array(self._pbounds, dtype=np.float64)
        self._space_params = np.empty(shape=(0, self._space_dim))
        self._space_target = np.empty(shape=0)

        self._opt_x_queue = Queue()
        self._opt_regressor = GaussianProcessRegressor(
            kernel=Matern(nu=2.5),
            alpha=1e-6,
            normalize_y=True,
            n_restarts_optimizer=5,
            random_state=self._random,
        )
        self._opt_regressor.set_params(**self.__algorithm.gp_params)

        self._is_fitted = Event()
        self._last_fit_position = 0
        self._fit_sample_lock = Lock()
        self._step_count, self._max_step = 0, self.__algorithm.max_steps

        acq, kappa, kappa_decay, kappa_decay_delay, xi = self.__algorithm.util_args
        self._util = UtilityFunction(acq, kappa, xi, kappa_decay, kappa_decay_delay)

    @property
    def opt_direction(self) -> OptimizeDirection:
        return self.__algorithm.opt_direction

    def _direction_postprocess(self, v):
        if self.opt_direction == OptimizeDirection.MAXIMIZE:
            return v
        elif self.opt_direction == OptimizeDirection.MINIMIZE:
            return -v
        else:
            assert False, f'Unknown optimization direction - {self.opt_direction!r}.'  # pragma: no cover

    def _create_new_sample(self) -> np.ndarray:
        with self._fit_sample_lock:
            if self._is_fitted.is_set():  # a new suggested sample
                # noinspection PyArgumentList
                return acq_max(
                    ac=self._util.utility,
                    gp=self._opt_regressor,
                    y_max=self._space_target.max(),
                    bounds=self._space_bounds,
                    random_state=self._random,
                )

            else:  # a new random sample
                data = np.empty((1, self._space_dim))
                for col, (lower, upper) in enumerate(self._space_bounds):
                    data.T[col] = self._random.uniform(lower, upper, size=1)
                return data.ravel()

    def _space_append(self, x: np.ndarray, y: float):
        self._space_params = np.concatenate([self._space_params, x.reshape(1, -1)])
        self._space_target = np.concatenate([self._space_target, [y]])

    def _space_fit(self):
        self._util.update_params()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self._opt_regressor.fit(self._space_params, self._space_target)

    def _return_on_success(self, task: Task, retval: Any):
        _, _, (x_probe,) = task
        y_value = retval.value

        with self._fit_sample_lock:
            self._space_append(x_probe, self._direction_postprocess(y_value))
            _total_count, = self._space_target.shape
            if (not self._is_fitted.is_set() and _total_count >= self.__algorithm.init_steps) or \
                    (self._is_fitted.is_set() and _total_count >= self._last_fit_position + self.__algorithm.fit_steps):
                self._space_fit()
                self._last_fit_position = _total_count
                self._is_fitted.set()

    def _run(self):
        while self._max_step is None or self._step_count < self._max_step:
            self._step_count += 1
            x_probe = self._create_new_sample()
            x_actual = tuple(func(xv) for xv, func in zip(x_probe, self._pfuncs))
            try:
                self._put_via_space(x_actual, (x_probe,))
            except ServiceNoLongerAccept:
                break
