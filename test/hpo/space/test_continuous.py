import pytest

from ditk.hpo.space import ContinuousSpace


@pytest.mark.unittest
class TestHpoContinuousFixed:
    def test_continuous_space(self):
        space = ContinuousSpace(0.4, 2.2)
        assert space.lbound == pytest.approx(0.4)
        assert space.rbound == pytest.approx(2.2)
        assert space.length == pytest.approx(1.8)
        assert space.count is None
