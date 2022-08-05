import numpy as np
import pytest
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern

from lighttuner.hpo.algorithm.bayes import UtilityFunction, acq_max, ensure_rng


def get_globals():
    _x = np.array(
        [
            [0.00, 0.00],
            [0.99, 0.99],
            [0.00, 0.99],
            [0.99, 0.00],
            [0.50, 0.50],
            [0.25, 0.50],
            [0.50, 0.25],
            [0.75, 0.50],
            [0.50, 0.75],
        ]
    )

    def get_y(x):
        return -(x[:, 0] - 0.3) ** 2 - 0.5 * (x[:, 1] - 0.6) ** 2 + 2

    y = get_y(_x)

    mesh = np.dstack(np.meshgrid(np.arange(0, 1, 0.005), np.arange(0, 1, 0.005))).reshape(-1, 2)

    gp = GaussianProcessRegressor(
        kernel=Matern(),
        n_restarts_optimizer=25,
    )
    gp.fit(_x, y)

    return {'x': _x, 'y': y, 'gp': gp, 'mesh': mesh}


def brute_force_maximum(mesh, gp, kind='ucb', kappa=1.0, xi=1.0):
    uf = UtilityFunction(kind=kind, kappa=kappa, xi=xi)

    mesh_vals = uf.utility(mesh, gp, 2)
    max_val = mesh_vals.max()
    max_arg_val = mesh[np.argmax(mesh_vals)]

    return max_val, max_arg_val


GLOB = get_globals()
X, Y, GP, MESH = GLOB['x'], GLOB['y'], GLOB['gp'], GLOB['mesh']


@pytest.mark.unittest
def test_utility_function():
    util = UtilityFunction(kind="ucb", kappa=1.0, xi=1.0)
    assert util.kind == "ucb"

    util = UtilityFunction(kind="ei", kappa=1.0, xi=1.0)
    assert util.kind == "ei"

    util = UtilityFunction(kind="poi", kappa=1.0, xi=1.0)
    assert util.kind == "poi"

    with pytest.raises(NotImplementedError):
        _ = UtilityFunction(kind="other", kappa=1.0, xi=1.0)


@pytest.mark.unittest
def test_acq_with_ucb():
    util = UtilityFunction(kind="ucb", kappa=1.0, xi=1.0)
    episilon = 1e-2
    y_max = 2.0

    max_arg = acq_max(util.utility, GP, y_max, bounds=np.array([[0, 1], [0, 1]]), random_state=ensure_rng(0), n_iter=20)
    _, brute_max_arg = brute_force_maximum(MESH, GP, kind='ucb', kappa=1.0, xi=1.0)

    assert all(abs(brute_max_arg - max_arg) < episilon)


@pytest.mark.unittest
def test_acq_with_ei():
    util = UtilityFunction(kind="ei", kappa=1.0, xi=1e-6)
    episilon = 1e-2
    y_max = 2.0

    max_arg = acq_max(
        util.utility,
        GP,
        y_max,
        bounds=np.array([[0, 1], [0, 1]]),
        random_state=ensure_rng(0),
        n_iter=200,
    )
    _, brute_max_arg = brute_force_maximum(MESH, GP, kind='ei', kappa=1.0, xi=1e-6)

    assert all(abs(brute_max_arg - max_arg) < episilon)


@pytest.mark.unittest
def test_acq_with_poi():
    util = UtilityFunction(kind="poi", kappa=1.0, xi=1e-4)
    episilon = 1e-2
    y_max = 2.0

    max_arg = acq_max(
        util.utility,
        GP,
        y_max,
        bounds=np.array([[0, 1], [0, 1]]),
        random_state=ensure_rng(0),
        n_iter=200,
    )
    _, brute_max_arg = brute_force_maximum(MESH, GP, kind='poi', kappa=1.0, xi=1e-4)

    assert all(abs(brute_max_arg - max_arg) < episilon)
