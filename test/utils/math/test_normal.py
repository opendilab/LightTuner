import math

import pytest

from ditk.utils.math import l2normal

EPS = 1e-12


@pytest.mark.unittest
class TestUtilsMatchNormal:
    def test_l2normal(self):
        assert l2normal(0.0) == -math.inf
        assert l2normal(1.0) == math.inf
        assert abs(l2normal(0.2) - (-0.8416212335729143)) < EPS
        assert l2normal(0.5) == 0.0
        assert abs(l2normal(0.8) - 0.8416212335729143) < EPS
