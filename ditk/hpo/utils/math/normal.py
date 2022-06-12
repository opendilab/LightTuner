import math

from scipy.special import erfinv

v_2_m1 = math.sqrt(2)


def l2normal(x, mu=0.0, sigma=1.0):
    """
    Overview:
        Turn one :math:`\\left[0, 1\\right]` linear value to normal distribution value, follows ``N(mu, sigma)``.

    :param x: Original linear value.
    :param mu: Mu value.
    :param sigma: Sigma value.
    :return: A normal distribution value.

    Examples::
        - Simple usage

        >>> from ditk.hpo.utils.math import l2normal
        >>> l2normal(0.0)
        -inf
        >>> l2normal(0.2)
        -0.8416212335729143
        >>> l2normal(0.5)
        0.0
        >>> l2normal(0.8)
        0.8416212335729143
        >>> l2normal(1.0)
        inf
        >>> l2normal(-0.1)
        nan
        >>> l2normal(1.1)
        nan

        - Use given ``mu`` and ``sigma``

        >>> l2normal(0.2, 2, 8)
        -4.732969868583314
        >>> l2normal(0.5, 10, 4)
        10.0
        >>> l2normal(0.8, -3, 6)
        2.0497274014374858
    """
    return mu + sigma * v_2_m1 * erfinv(2 * x - 1)
