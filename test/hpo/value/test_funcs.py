import pytest

from ditk.hpo import uniform, quniform, choice, randint
from ditk.hpo.space import ContinuousSpace, SeparateSpace, FixedSpace


@pytest.mark.unittest
class TestHpoValueFuncs:
    def test_uniform(self):
        value = uniform(-10, 20.2)
        assert isinstance(value.space, ContinuousSpace)
        assert value.space.lbound == pytest.approx(-10.0)
        assert value.space.ubound == pytest.approx(20.2)
        assert value.trans(-10) == pytest.approx(-10.0)
        assert value.trans(10) == pytest.approx(10.0)
        assert value.trans(20.2) == pytest.approx(20.2)

        with pytest.raises(ValueError):
            uniform(-10, -10)
        with pytest.raises(ValueError):
            uniform(-10, -10.1)

    def test_quniform(self):
        value = quniform(-10, 20.2, 0.2)
        assert isinstance(value.space, SeparateSpace)
        assert value.space.start == pytest.approx(-10.0)
        assert value.space.end == pytest.approx(20.2)
        assert value.space.step == pytest.approx(0.2)
        assert value.trans(-10) == pytest.approx(-10.0)
        assert value.trans(10) == pytest.approx(10.0)
        assert value.trans(20.2) == pytest.approx(20.2)

        with pytest.raises(ValueError):
            quniform(-10, 20.2, -0.2)
        with pytest.raises(ValueError):
            quniform(-10, -20.2, -0.2)
        with pytest.raises(ValueError):
            quniform(-10, -20.2, 0.2)

    def test_choice(self):
        value = choice(['a', 'b', 'c'])
        assert isinstance(value.space, FixedSpace)
        assert value.space.count == 3
        assert value.space.length == 3
        assert value.trans(0) == 'a'
        assert value.trans(1) == 'b'
        assert value.trans(2) == 'c'

        with pytest.raises(ValueError):
            choice([])
        with pytest.raises(TypeError):
            choice({'a', 'b', 'c'})

    def test_randint(self):
        value = randint(10.1, 20.2)
        assert isinstance(value.space, SeparateSpace)
        assert value.space.start == pytest.approx(11.0)
        assert value.space.end == pytest.approx(20.0)
        assert value.space.step == pytest.approx(1.0)
        assert value.trans(11.9) == pytest.approx(11)
        assert value.trans(10) == pytest.approx(10)
        assert value.trans(20.2) == pytest.approx(20)
