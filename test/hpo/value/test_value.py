import pytest

from ditk.hpo.space import ContinuousSpace
from ditk.hpo.value import HyperValue


# noinspection DuplicatedCode
@pytest.mark.unittest
class TestHpoValueValue:
    def test_base_continuous(self):
        space = ContinuousSpace(0.4, 2.2)
        v = HyperValue(space)
        assert v.space is space

        assert v.allocate() == pytest.approx((0.4, 0.85, 1.3, 1.75, 2.2))
        assert v.allocate(0) == pytest.approx(())
        assert v.allocate(1) == pytest.approx((1.3,))
        assert v.allocate(2) == pytest.approx((0.4, 2.2))
        assert v.allocate(3) == pytest.approx((0.4, 1.3, 2.2))
        assert v.allocate(5) == pytest.approx((0.4, 0.85, 1.3, 1.75, 2.2))
        assert v.allocate(7) == pytest.approx((0.4, 0.7, 1.0, 1.3, 1.6, 1.9, 2.2))
        assert v.allocate(10) == pytest.approx((0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2))

    def test_chain(self):
        v = HyperValue(ContinuousSpace(0.4, 2.2)) >> (lambda x: (x + 2) ** 2) >> round >> int
        assert v.allocate() == pytest.approx((6, 8, 11, 14, 18))
        assert v.allocate(0) == pytest.approx(())
        assert v.allocate(1) == pytest.approx((11,))
        assert v.allocate(2) == pytest.approx((6, 18))
        assert v.allocate(3) == pytest.approx((6, 11, 18))
        assert v.allocate(5) == pytest.approx((6, 8, 11, 14, 18))
        assert v.allocate(7) == pytest.approx((6, 7, 9, 11, 13, 15, 18))
        assert v.allocate(10) == pytest.approx((6, 7, 8, 9, 10, 12, 13, 14, 16, 18))

    def test_add(self):
        v = HyperValue(ContinuousSpace(0.4, 2.2)) + 1
        assert v.allocate() == pytest.approx((1.4, 1.85, 2.3, 2.75, 3.2))
        assert v.allocate(0) == pytest.approx(())
        assert v.allocate(1) == pytest.approx((2.3,))
        assert v.allocate(2) == pytest.approx((1.4, 3.2))
        assert v.allocate(3) == pytest.approx((1.4, 2.3, 3.2))
        assert v.allocate(5) == pytest.approx((1.4, 1.85, 2.3, 2.75, 3.2))
        assert v.allocate(7) == pytest.approx((1.4, 1.7, 2.0, 2.3, 2.6, 2.9, 3.2))
        assert v.allocate(10) == pytest.approx((1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.2))

    def test_radd(self):
        v = 1 + HyperValue(ContinuousSpace(0.4, 2.2))
        assert v.allocate() == pytest.approx((1.4, 1.85, 2.3, 2.75, 3.2))
        assert v.allocate(0) == pytest.approx(())
        assert v.allocate(1) == pytest.approx((2.3,))
        assert v.allocate(2) == pytest.approx((1.4, 3.2))
        assert v.allocate(3) == pytest.approx((1.4, 2.3, 3.2))
        assert v.allocate(5) == pytest.approx((1.4, 1.85, 2.3, 2.75, 3.2))
        assert v.allocate(7) == pytest.approx((1.4, 1.7, 2.0, 2.3, 2.6, 2.9, 3.2))
        assert v.allocate(10) == pytest.approx((1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.2))

    def test_sub(self):
        v = HyperValue(ContinuousSpace(0.4, 2.2)) - 1
        assert v.allocate() == pytest.approx((-0.6, -0.15, 0.3, 0.75, 1.2))
        assert v.allocate(0) == pytest.approx(())
        assert v.allocate(1) == pytest.approx((0.3,))
        assert v.allocate(2) == pytest.approx((-0.6, 1.2))
        assert v.allocate(3) == pytest.approx((-0.6, 0.3, 1.2))
        assert v.allocate(5) == pytest.approx((-0.6, -0.15, 0.3, 0.75, 1.2))
        assert v.allocate(7) == pytest.approx((-0.6, -0.3, 0.0, 0.3, 0.6, 0.9, 1.2))
        assert v.allocate(10) == pytest.approx((-0.6, -0.4, -0.2, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2))

    def test_rsub(self):
        v = 1 - HyperValue(ContinuousSpace(0.4, 2.2))
        assert v.allocate() == pytest.approx((0.6, 0.15, -0.3, -0.75, -1.2))
        assert v.allocate(0) == pytest.approx(())
        assert v.allocate(1) == pytest.approx((-0.3,))
        assert v.allocate(2) == pytest.approx((0.6, -1.2))
        assert v.allocate(3) == pytest.approx((0.6, -0.3, -1.2))
        assert v.allocate(5) == pytest.approx((0.6, 0.15, -0.3, -0.75, -1.2))
        assert v.allocate(7) == pytest.approx((0.6, 0.3, 0.0, -0.3, -0.6, -0.9, -1.2))
        assert v.allocate(10) == pytest.approx((0.6, 0.4, 0.2, 0.0, -0.2, -0.4, -0.6, -0.8, -1.0, -1.2))

    def test_mul(self):
        v = HyperValue(ContinuousSpace(0.4, 2.2)) * 2
        assert v.allocate() == pytest.approx((0.8, 1.7, 2.6, 3.5, 4.4))
        assert v.allocate(0) == pytest.approx(())
        assert v.allocate(1) == pytest.approx((2.6,))
        assert v.allocate(2) == pytest.approx((0.8, 4.4))
        assert v.allocate(3) == pytest.approx((0.8, 2.6, 4.4))
        assert v.allocate(5) == pytest.approx((0.8, 1.7, 2.6, 3.5, 4.4))
        assert v.allocate(7) == pytest.approx((0.8, 1.4, 2.0, 2.6, 3.2, 3.8, 4.4))
        assert v.allocate(10) == pytest.approx((0.8, 1.2, 1.6, 2.0, 2.4, 2.8, 3.2, 3.6, 4.0, 4.4))

    def test_rmul(self):
        v = 2 * HyperValue(ContinuousSpace(0.4, 2.2))
        assert v.allocate() == pytest.approx((0.8, 1.7, 2.6, 3.5, 4.4))
        assert v.allocate(0) == pytest.approx(())
        assert v.allocate(1) == pytest.approx((2.6,))
        assert v.allocate(2) == pytest.approx((0.8, 4.4))
        assert v.allocate(3) == pytest.approx((0.8, 2.6, 4.4))
        assert v.allocate(5) == pytest.approx((0.8, 1.7, 2.6, 3.5, 4.4))
        assert v.allocate(7) == pytest.approx((0.8, 1.4, 2.0, 2.6, 3.2, 3.8, 4.4))
        assert v.allocate(10) == pytest.approx((0.8, 1.2, 1.6, 2.0, 2.4, 2.8, 3.2, 3.6, 4.0, 4.4))

    def test_truediv(self):
        v = HyperValue(ContinuousSpace(0.4, 2.2)) / 2
        assert v.allocate() == pytest.approx((0.2, 0.425, 0.65, 0.875, 1.1))
        assert v.allocate(0) == pytest.approx(())
        assert v.allocate(1) == pytest.approx((0.65,))
        assert v.allocate(2) == pytest.approx((0.2, 1.1))
        assert v.allocate(3) == pytest.approx((0.2, 0.65, 1.1))
        assert v.allocate(5) == pytest.approx((0.2, 0.425, 0.65, 0.875, 1.1))
        assert v.allocate(7) == pytest.approx((0.2, 0.35, 0.5, 0.65, 0.8, 0.95, 1.1))
        assert v.allocate(10) == pytest.approx((0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1))

    def test_rtruediv(self):
        v = 2 / HyperValue(ContinuousSpace(0.4, 2.2))
        assert v.allocate() == pytest.approx(
            (5.0, 2.352941176470588, 1.538461538461538, 1.1428571428571428, 0.9090909090909091))
        assert v.allocate(0) == pytest.approx(())
        assert v.allocate(1) == pytest.approx((1.5384615384615383,))
        assert v.allocate(2) == pytest.approx((5.0, 0.9090909090909091))
        assert v.allocate(3) == pytest.approx((5.0, 1.538461538461538, 0.9090909090909091))
        assert v.allocate(5) == pytest.approx(
            (5.0, 2.352941176470588, 1.538461538461538, 1.1428571428571428, 0.9090909090909091))
        assert v.allocate(7) == pytest.approx(
            (5.0, 2.8571428571428568, 2.0, 1.538461538461538, 1.25, 1.0526315789473681, 0.9090909090909091))
        assert v.allocate(10) == pytest.approx(
            (5.0, 3.333333333333333, 2.5, 2.0, 1.6666666666666665, 1.4285714285714282,
             1.25, 1.111111111111111, 1.0, 0.9090909090909091))

    def test_floordiv(self):
        v = HyperValue(ContinuousSpace(0.4, 2.2)) // 0.5
        assert v.allocate() == pytest.approx((0.0, 1.0, 2.0, 3.0, 4.0))
        assert v.allocate(0) == pytest.approx(())
        assert v.allocate(1) == pytest.approx((2.0,))
        assert v.allocate(2) == pytest.approx((0.0, 4.0))
        assert v.allocate(3) == pytest.approx((0.0, 2.0, 4.0))
        assert v.allocate(5) == pytest.approx((0.0, 1.0, 2.0, 3.0, 4.0))
        assert v.allocate(7) == pytest.approx((0.0, 1.0, 2.0, 2.0, 3.0, 3.0, 4.0))
        assert v.allocate(10) == pytest.approx((0.0, 1.0, 1.0, 2.0, 2.0, 2.0, 3.0, 3.0, 4.0, 4.0))

    def test_rfloordiv(self):
        v = 5.0 // HyperValue(ContinuousSpace(0.4, 2.2))
        assert v.allocate() == pytest.approx((12.0, 5.0, 3.0, 2.0, 2.0))
        assert v.allocate(0) == pytest.approx(())
        assert v.allocate(1) == pytest.approx((3.0,))
        assert v.allocate(2) == pytest.approx((12.0, 2.0))
        assert v.allocate(3) == pytest.approx((12.0, 3.0, 2.0))
        assert v.allocate(5) == pytest.approx((12.0, 5.0, 3.0, 2.0, 2.0))
        assert v.allocate(7) == pytest.approx((12.0, 7.0, 5.0, 3.0, 3.0, 2.0, 2.0))
        assert v.allocate(10) == pytest.approx((12.0, 8.0, 6.0, 5.0, 4.0, 3.0, 3.0, 2.0, 2.0, 2.0))

    def test_mod(self):
        v = HyperValue(ContinuousSpace(0.4, 2.2)) % 0.5
        assert v.allocate() == pytest.approx((0.4, 0.35, 0.3, 0.25, 0.2))
        assert v.allocate(0) == pytest.approx(())
        assert v.allocate(1) == pytest.approx((0.3,))
        assert v.allocate(2) == pytest.approx((0.4, 0.2))
        assert v.allocate(3) == pytest.approx((0.4, 0.3, 0.2))
        assert v.allocate(5) == pytest.approx((0.4, 0.35, 0.3, 0.25, 0.2))
        assert v.allocate(7) == pytest.approx((0.4, 0.2, 0.0, 0.3, 0.1, 0.4, 0.2))
        assert v.allocate(10) == pytest.approx((0.4, 0.1, 0.3, 0.0, 0.2, 0.4, 0.1, 0.3, 0.0, 0.2))

    def test_rmod(self):
        v = 5.0 % HyperValue(ContinuousSpace(0.4, 2.2))
        assert v.allocate() == pytest.approx((0.2, 0.75, 1.1, 1.5, 0.6))
        assert v.allocate(0) == pytest.approx(())
        assert v.allocate(1) == pytest.approx((1.1,))
        assert v.allocate(2) == pytest.approx((0.2, 0.6))
        assert v.allocate(3) == pytest.approx((0.2, 1.1, 0.6))
        assert v.allocate(5) == pytest.approx((0.2, 0.75, 1.1, 1.5, 0.6))
        assert v.allocate(7) == pytest.approx((0.2, 0.1, 0.0, 1.1, 0.2, 1.2, 0.6))
        assert v.allocate(10) == pytest.approx((0.2, 0.2, 0.2, 0.0, 0.2, 0.8, 0.2, 1.4, 1.0, 0.6))

    def test_pow(self):
        v = HyperValue(ContinuousSpace(0.4, 2.2)) ** 2
        assert v.allocate() == pytest.approx((0.16, 0.7225, 1.69, 3.0625, 4.84))
        assert v.allocate(0) == pytest.approx(())
        assert v.allocate(1) == pytest.approx((1.69,))
        assert v.allocate(2) == pytest.approx((0.16, 4.84))
        assert v.allocate(3) == pytest.approx((0.16, 1.69, 4.84))
        assert v.allocate(5) == pytest.approx((0.16, 0.7225, 1.69, 3.0625, 4.84))
        assert v.allocate(7) == pytest.approx((0.16, 0.49, 1.0, 1.69, 2.56, 3.61, 4.84))
        assert v.allocate(10) == pytest.approx((0.16, 0.36, 0.64, 1.0, 1.44, 1.96, 2.56, 3.24, 4.0, 4.84))

    def test_rpow(self):
        v = 2 ** HyperValue(ContinuousSpace(0.4, 2.2))
        assert v.allocate() == pytest.approx(
            (1.3195079107728942, 1.8025009252216606, 2.462288826689833, 3.363585661014858, 4.59479341998814))
        assert v.allocate(0) == pytest.approx(())
        assert v.allocate(1) == pytest.approx((2.4622888266898326,))
        assert v.allocate(2) == pytest.approx((1.3195079107728942, 4.59479341998814))
        assert v.allocate(3) == pytest.approx((1.3195079107728942, 2.462288826689833, 4.59479341998814))
        assert v.allocate(5) == pytest.approx(
            (1.3195079107728942, 1.8025009252216606, 2.462288826689833, 3.363585661014858, 4.59479341998814))
        assert v.allocate(7) == pytest.approx((1.3195079107728942, 1.6245047927124712, 2.0, 2.462288826689833,
                                               3.0314331330207964, 3.7321319661472305, 4.59479341998814))
        assert v.allocate(10) == pytest.approx((1.3195079107728942, 1.5157165665103982, 1.7411011265922482, 2.0,
                                                2.29739670999407, 2.6390158215457893, 3.0314331330207964,
                                                3.4822022531844974, 4.0, 4.59479341998814))

    def test_pos(self):
        v = +HyperValue(ContinuousSpace(0.4, 2.2))
        assert v.allocate() == pytest.approx((0.4, 0.85, 1.3, 1.75, 2.2))
        assert v.allocate(0) == pytest.approx(())
        assert v.allocate(1) == pytest.approx((1.3,))
        assert v.allocate(2) == pytest.approx((0.4, 2.2))
        assert v.allocate(3) == pytest.approx((0.4, 1.3, 2.2))
        assert v.allocate(5) == pytest.approx((0.4, 0.85, 1.3, 1.75, 2.2))
        assert v.allocate(7) == pytest.approx((0.4, 0.7, 1.0, 1.3, 1.6, 1.9, 2.2))
        assert v.allocate(10) == pytest.approx((0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2))

    def test_neg(self):
        v = -HyperValue(ContinuousSpace(0.4, 2.2))
        assert v.allocate() == pytest.approx((-0.4, -0.85, -1.3, -1.75, -2.2))
        assert v.allocate(0) == pytest.approx(())
        assert v.allocate(1) == pytest.approx((-1.3,))
        assert v.allocate(2) == pytest.approx((-0.4, -2.2))
        assert v.allocate(3) == pytest.approx((-0.4, -1.3, -2.2))
        assert v.allocate(5) == pytest.approx((-0.4, -0.85, -1.3, -1.75, -2.2))
        assert v.allocate(7) == pytest.approx((-0.4, -0.7, -1.0, -1.3, -1.6, -1.9, -2.2))
        assert v.allocate(10) == pytest.approx((-0.4, -0.6, -0.8, -1.0, -1.2, -1.4, -1.6, -1.8, -2.0, -2.2))
