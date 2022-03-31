import pytest

from ditk.hpo.space import SeparateSpace


@pytest.mark.unittest
class TestHpoSeparateFixed:
    def test_separate_space(self):
        space = SeparateSpace(0.4, 2.2, 0.2)
        assert space.lbound == pytest.approx(0.4)
        assert space.rbound == pytest.approx(2.2)
        assert space.length == pytest.approx(1.8)

    def test_allocate(self):
        space = SeparateSpace(0.4, 2.2, 0.2)
        assert space.allocate() == pytest.approx((0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2))
        assert space.allocate(0) == pytest.approx(())
        assert space.allocate(1) == pytest.approx((1.2,))
        assert space.allocate(2) == pytest.approx((0.4, 2.2))
        assert space.allocate(3) == pytest.approx((0.4, 1.2, 2.2))
        assert space.allocate(4) == pytest.approx((0.4, 1.0, 1.6, 2.2))
        assert space.allocate(5) == pytest.approx((0.4, 0.8, 1.2, 1.8, 2.2))
        assert space.allocate(6) == pytest.approx((0.4, 0.8, 1.2, 1.4, 1.8, 2.2))
        assert space.allocate(7) == pytest.approx((0.4, 0.8, 1.0, 1.2, 1.6, 2.0, 2.2))
        assert space.allocate(8) == pytest.approx((0.4, 0.6, 1.0, 1.2, 1.4, 1.6, 2.0, 2.2))
        assert space.allocate(9) == pytest.approx((0.4, 0.6, 0.8, 1.0, 1.2, 1.6, 1.8, 2.0, 2.2))
        assert space.allocate(10) == pytest.approx((0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2))
        assert space.allocate(11) == pytest.approx((0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2))
        assert space.allocate(15) == pytest.approx((0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2))
        assert space.allocate(100) == pytest.approx((0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2))
