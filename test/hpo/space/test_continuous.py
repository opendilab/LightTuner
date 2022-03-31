import pytest

from ditk.hpo.space import ContinuousSpace


@pytest.mark.unittest
class TestHpoContinuousFixed:
    def test_continuous_space(self):
        space = ContinuousSpace(0.4, 2.2)
        assert space.lbound == pytest.approx(0.4)
        assert space.rbound == pytest.approx(2.2)
        assert space.length == pytest.approx(1.8)

    def test_allocate(self):
        space = ContinuousSpace(0.4, 2.2)
        assert space.allocate() == pytest.approx((0.4, 0.85, 1.3, 1.75, 2.2))
        assert space.allocate(0) == pytest.approx(())
        assert space.allocate(1) == pytest.approx((1.3,))
        assert space.allocate(2) == pytest.approx((0.4, 2.2))
        assert space.allocate(3) == pytest.approx((0.4, 1.3, 2.2))
        assert space.allocate(4) == pytest.approx((0.4, 1.0, 1.6, 2.2))
        assert space.allocate(5) == pytest.approx((0.4, 0.85, 1.3, 1.75, 2.2))
        assert space.allocate(6) == pytest.approx((0.4, 0.76, 1.12, 1.48, 1.84, 2.2))
        assert space.allocate(7) == pytest.approx((0.4, 0.7, 1.0, 1.3, 1.6, 1.9, 2.2))
        assert space.allocate(8) == pytest.approx((0.4, 0.6571428571428573, 0.9142857142857144, 1.1714285714285715,
                                                   1.4285714285714288, 1.685714285714286, 1.942857142857143, 2.2))
        assert space.allocate(9) == pytest.approx((0.4, 0.625, 0.85, 1.075, 1.3, 1.525, 1.75, 1.975, 2.2))
        assert space.allocate(10) == pytest.approx((0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2))
        assert space.allocate(11) == pytest.approx((0.4, 0.58, 0.76, 0.94, 1.12, 1.3, 1.48, 1.66, 1.84, 2.02, 2.2))
