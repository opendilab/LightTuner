import math

import pytest

from ditk.hpo.utils import erfinv


@pytest.mark.unittest
class TestHpoUtilsMathErfinv:
    def test_erfinv(self):
        assert erfinv(1) == math.inf
        assert erfinv(-1) == -math.inf
        assert erfinv(1 - 1e-16) == math.inf
        assert erfinv(-1 + 1e-17) == -math.inf
        assert erfinv(0) == pytest.approx(0)

        assert erfinv(0.2) == pytest.approx(0.1791434546212916)
        assert erfinv(0.5) == pytest.approx(0.4769362762044698)
        assert erfinv(0.8) == pytest.approx(0.9061938024368231)

        assert erfinv(-0.2) == pytest.approx(-0.1791434546212916)
        assert erfinv(-0.5) == pytest.approx(-0.4769362762044698)
        assert erfinv(-0.8) == pytest.approx(-0.9061938024368231)

        assert math.isnan(erfinv(-1.2))
        assert math.isnan(erfinv(1.2))
