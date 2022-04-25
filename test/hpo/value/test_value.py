import pytest

from ditk.hpo.space import ContinuousSpace
from ditk.hpo.value import HyperValue


@pytest.mark.unittest
class TestHpoValueValue:
    def test_common(self):
        space = ContinuousSpace(0, 10)
        value = HyperValue(space)
        assert value.space is space
        assert value.trans(1) == 1
        assert value.trans(5) == 5

    def test_common_with_init(self):
        space = ContinuousSpace(0, 10)
        value = HyperValue(space, [
            (lambda x: 2 ** x)
        ])
        assert value.space is space
        assert value.trans(1) == 2
        assert value.trans(5) == 32

    def test_pipe(self):
        space = ContinuousSpace(0, 10)
        value = HyperValue(space) >> (lambda x: 2 ** x) >> float
        assert value.space is space
        assert isinstance(value.trans(1), float)
        assert value.trans(1) == pytest.approx(2.0)
        assert isinstance(value.trans(5), float)
        assert value.trans(5) == pytest.approx(32.0)

    def test_add(self):
        space = ContinuousSpace(0, 10)
        value = HyperValue(space) + 1
        assert value.space is space
        assert value.trans(1) == 2
        assert value.trans(5) == 6

        value = 1 + HyperValue(space)
        assert value.space is space
        assert value.trans(1) == 2
        assert value.trans(5) == 6

    def test_sub(self):
        space = ContinuousSpace(0, 10)
        value = HyperValue(space) - 2
        assert value.space is space
        assert value.trans(1) == -1
        assert value.trans(5) == 3

        value = 2 - HyperValue(space)
        assert value.space is space
        assert value.trans(1) == 1
        assert value.trans(5) == -3

    def test_mul(self):
        space = ContinuousSpace(0, 10)
        value = HyperValue(space) * 2
        assert value.space is space
        assert value.trans(1) == 2
        assert value.trans(5) == 10

        value = 2 * HyperValue(space)
        assert value.space is space
        assert value.trans(1) == 2
        assert value.trans(5) == 10

    def test_truediv(self):
        space = ContinuousSpace(0, 10)
        value = HyperValue(space) / 2
        assert value.space is space
        assert value.trans(1) == pytest.approx(0.5)
        assert value.trans(5) == pytest.approx(2.5)

        value = 2 / HyperValue(space)
        assert value.space is space
        assert value.trans(1) == pytest.approx(2.0)
        assert value.trans(5) == pytest.approx(0.4)

    def test_floordiv(self):
        space = ContinuousSpace(0, 10)
        value = HyperValue(space) // 2
        assert value.space is space
        assert value.trans(1) == pytest.approx(0.0)
        assert value.trans(5) == pytest.approx(2.0)

        value = 2 // HyperValue(space)
        assert value.space is space
        assert value.trans(1) == pytest.approx(2.0)
        assert value.trans(5) == pytest.approx(0.0)

    def test_mod(self):
        space = ContinuousSpace(0, 10)
        value = HyperValue(space) % 3
        assert value.space is space
        assert value.trans(1) == 1
        assert value.trans(5) == 2

        value = 22 % HyperValue(space)
        assert value.space is space
        assert value.trans(2) == 0
        assert value.trans(5) == 2

    def test_pow(self):
        space = ContinuousSpace(0, 10)
        value = HyperValue(space) ** 2
        assert value.space is space
        assert value.trans(1) == 1
        assert value.trans(5) == 25

        value = 2 ** HyperValue(space)
        assert value.space is space
        assert value.trans(1) == 2
        assert value.trans(5) == 32

    def test_pos(self):
        space = ContinuousSpace(0, 10)
        value = +HyperValue(space)
        assert value.space is space
        assert value.trans(1) == 1
        assert value.trans(-5) == -5

    def test_neg(self):
        space = ContinuousSpace(0, 10)
        value = -HyperValue(space)
        assert value.space is space
        assert value.trans(1) == -1
        assert value.trans(-5) == 5
