import warnings

import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm


def acq_max(ac, gp, y_max, bounds, random_state, n_warmup=10000, n_iter=10):
    """
    Overview:
        A function to find the maximum of the acquisition function.

        It uses a combination of random sampling (cheap) and the 'L-BFGS-B' \
        optimization method. First by sampling `n_warmup` (1e5) points at random, \
        and then running L-BFGS-B from `n_iter` (250) random starting points.

    :param ac: The acquisition function object that return its point-wise value.
    :param gp: A gaussian process fitted to the relevant data.
    :param y_max: The current maximum known value of the target function.
    :param bounds: The variables bounds to limit the search of the acq max.
    :param random_state: instance of np.RandomState random number generator
    :param n_warmup: number of times to randomly sample the acquisition function
    :param n_iter: number of times to run ``scipy.minimize``.
    :return: x_max, The arg max of the acquisition function.
    """

    # Warm up with random points
    x_tries = random_state.uniform(bounds[:, 0], bounds[:, 1], size=(n_warmup, bounds.shape[0]))
    ys = ac(x_tries, gp=gp, y_max=y_max)
    x_max = x_tries[ys.argmax()]
    max_acq = ys.max()

    # Explore the parameter space more thoroughly
    x_seeds = random_state.uniform(bounds[:, 0], bounds[:, 1], size=(n_iter, bounds.shape[0]))
    for x_try in x_seeds:
        # Find the minimum of minus the acquisition function
        res = minimize(
            lambda x: -ac(x.reshape(1, -1), gp=gp, y_max=y_max),
            x_try.reshape(1, -1),
            bounds=bounds,
            method="L-BFGS-B"
        )

        # See if success
        if not res.success:
            continue

        # Store it if better than previous minimum(maximum).
        try:  # for scipy<1.8
            fun = -res.fun[0]
        except TypeError:  # for scipy>=1.8
            fun = -res.fun
        if max_acq is None or -fun >= max_acq:
            x_max = res.x
            max_acq = fun

    # Clip output to make sure it lies within the bounds. Due to floating
    # point technicalities this is not always the case.
    return np.clip(x_max, bounds[:, 0], bounds[:, 1])


class UtilityFunction:
    """
    Overview:
        An object to compute the acquisition functions.
    """

    def __init__(self, kind, kappa, xi, kappa_decay=1, kappa_decay_delay=0):
        self.kappa = kappa
        self._kappa_decay = kappa_decay
        self._kappa_decay_delay = kappa_decay_delay
        self.xi = xi

        self._iters_counter = 0
        if kind not in ['ucb', 'ei', 'poi']:
            raise NotImplementedError(
                f"The utility function {kind} has not been implemented, "
                f"please choose one of ucb, ei, or poi."
            )
        else:
            self.kind = kind

    def update_params(self):
        self._iters_counter += 1
        if self._kappa_decay < 1 and self._iters_counter > self._kappa_decay_delay:
            self.kappa *= self._kappa_decay

    def utility(self, x, gp, y_max):
        if self.kind == 'ucb':
            return self._ucb(x, gp, self.kappa)
        elif self.kind == 'ei':
            return self._ei(x, gp, y_max, self.xi)
        elif self.kind == 'poi':
            return self._poi(x, gp, y_max, self.xi)
        else:
            raise ValueError(f'Unknown kind - {self.kind!r}.')  # pragma: no cover

    @staticmethod
    def _ucb(x, gp, kappa):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mean, std = gp.predict(x, return_std=True)

        return mean + kappa * std

    @staticmethod
    def _ei(x, gp, y_max, xi):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mean, std = gp.predict(x, return_std=True)

        a = (mean - y_max - xi)
        z = a / std
        return a * norm.cdf(z) + std * norm.pdf(z)

    @staticmethod
    def _poi(x, gp, y_max, xi):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mean, std = gp.predict(x, return_std=True)

        z = (mean - y_max - xi) / std
        return norm.cdf(z)


def ensure_rng(state=None):
    """
    Overview:
        Creates a random number generator based on an optional seed. This can be \
        an integer or another random state for a seeded rng, or None for an unseeded rng.

    :param state: Random state. If integer is given, it will be used as the random seed. If \
        ``np.random.RandomState`` is given, it will be directly used. Default is ``None`` which means \
        use the unseeded random generator.
    """
    if state is None:
        return np.random.RandomState()
    elif isinstance(state, int):
        return np.random.RandomState(state)
    elif isinstance(state, np.random.RandomState):
        return state
    else:
        raise TypeError(f'Unknown random state type - {repr(state)}.')
