import math

import pytest

from ditk.hpo.utils.math import l2normal

EPS = 1e-12


@pytest.mark.unittest
class TestHpoUtilsMatchNormal:

    def test_l2normal(self):
        assert l2normal(0.0) == -math.inf
        assert l2normal(1.0) == math.inf
        assert l2normal(0.2) == pytest.approx(-0.8416212335729143)
        assert l2normal(0.5) == pytest.approx(0.0)
        assert l2normal(0.8) == pytest.approx(0.8416212335729143)
