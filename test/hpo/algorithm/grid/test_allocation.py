import pytest

from ditk.hpo.algorithm.grid import allocate_continuous, allocate_separate, allocate_fixed
from ditk.hpo.space import ContinuousSpace, SeparateSpace, FixedSpace


# noinspection DuplicatedCode
@pytest.mark.unittest
class TestHpoAlgorithmGridAllocation:

    def test_allocate_continuous(self):
        space = ContinuousSpace(0.4, 2.2)
        assert allocate_continuous(space, 0) == pytest.approx(())
        assert allocate_continuous(space, 1) == pytest.approx((1.3, ))
        assert allocate_continuous(space, 2) == pytest.approx((0.4, 2.2))
        assert allocate_continuous(space, 3) == pytest.approx((0.4, 1.3, 2.2))
        assert allocate_continuous(space, 4) == pytest.approx((0.4, 1.0, 1.6, 2.2))
        assert allocate_continuous(space, 5) == pytest.approx((0.4, 0.85, 1.3, 1.75, 2.2))
        assert allocate_continuous(space, 6) == pytest.approx((0.4, 0.76, 1.12, 1.48, 1.84, 2.2))
        assert allocate_continuous(space, 7) == pytest.approx((0.4, 0.7, 1.0, 1.3, 1.6, 1.9, 2.2))
        assert allocate_continuous(space, 8) == pytest.approx(
            (
                0.4, 0.6571428571428573, 0.9142857142857144, 1.1714285714285715, 1.4285714285714288, 1.685714285714286,
                1.942857142857143, 2.2
            )
        )
        assert allocate_continuous(space, 9) == pytest.approx((0.4, 0.625, 0.85, 1.075, 1.3, 1.525, 1.75, 1.975, 2.2))
        assert allocate_continuous(space, 10) == pytest.approx((0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2))
        assert allocate_continuous(space, 11) == pytest.approx(
            (0.4, 0.58, 0.76, 0.94, 1.12, 1.3, 1.48, 1.66, 1.84, 2.02, 2.2)
        )

    def test_allocate_separate(self):
        space = SeparateSpace(0.4, 2.2, 0.2)
        assert allocate_separate(space, 0) == pytest.approx(())
        assert allocate_separate(space, 1) == pytest.approx((1.2, ))
        assert allocate_separate(space, 2) == pytest.approx((0.4, 2.2))
        assert allocate_separate(space, 3) == pytest.approx((0.4, 1.2, 2.2))
        assert allocate_separate(space, 4) == pytest.approx((0.4, 1.0, 1.6, 2.2))
        assert allocate_separate(space, 5) == pytest.approx((0.4, 0.8, 1.2, 1.8, 2.2))
        assert allocate_separate(space, 6) == pytest.approx((0.4, 0.8, 1.2, 1.4, 1.8, 2.2))
        assert allocate_separate(space, 7) == pytest.approx((0.4, 0.8, 1.0, 1.2, 1.6, 2.0, 2.2))
        assert allocate_separate(space, 8) == pytest.approx((0.4, 0.6, 1.0, 1.2, 1.4, 1.6, 2.0, 2.2))
        assert allocate_separate(space, 9) == pytest.approx((0.4, 0.6, 0.8, 1.0, 1.2, 1.6, 1.8, 2.0, 2.2))
        assert allocate_separate(space, 10) == pytest.approx((0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2))
        assert allocate_separate(space, 11) == pytest.approx((0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2))
        assert allocate_separate(space, 15) == pytest.approx((0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2))
        assert allocate_separate(space, 100) == pytest.approx((0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2))

    def test_allocate_fixed(self):
        space = FixedSpace(5)
        assert allocate_fixed(space) == (0, 1, 2, 3, 4)
