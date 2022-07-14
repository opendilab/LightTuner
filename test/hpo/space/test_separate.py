import pytest

from ditk.hpo.space import SeparateSpace


@pytest.mark.unittest
class TestHpoSpaceSeparate:

    def test_separate_space(self):
        space = SeparateSpace(0.4, 2.2, 0.4)
        assert space.start == pytest.approx(0.4)
        assert space.end == pytest.approx(2.0)
        assert space.step == pytest.approx(0.4)
        assert space.length == pytest.approx(1.6)
        assert space.count == 5
