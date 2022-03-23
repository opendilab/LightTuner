import math

import pytest

from ditk.utils import erfinv

EPS = 1e-12


@pytest.mark.unittest
class TestUtilsMathErfinv:
    def test_erfinv(self):
        assert erfinv(1) == math.inf
        assert erfinv(-1) == -math.inf
        assert erfinv(1 - 1e-16) == math.inf
        assert erfinv(-1 + 1e-17) == -math.inf
        assert abs(erfinv(0) - 0) < EPS

        assert abs(erfinv(0.2) - 0.1791434546212916) < EPS
        assert abs(erfinv(0.5) - 0.4769362762044698) < EPS
        assert abs(erfinv(0.8) - 0.9061938024368231) < EPS

        assert abs(erfinv(-0.2) - (-0.1791434546212916)) < EPS
        assert abs(erfinv(-0.5) - (-0.4769362762044698)) < EPS
        assert abs(erfinv(-0.8) - (-0.9061938024368231)) < EPS

        assert math.isnan(erfinv(-1.2))
        assert math.isnan(erfinv(1.2))
