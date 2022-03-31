import pytest

from ditk.hpo.space import FixedSpace


@pytest.mark.unittest
class TestHpoSpaceFixed:
    def test_fixed_space(self):
        space = FixedSpace(5)
        assert space.lbound == 0
        assert space.rbound == 4
        assert space.length == 5

    def test_allocate(self):
        space = FixedSpace(5)
        assert space.allocate() == (0, 1, 2, 3, 4)
        assert space.allocate(0) == (0, 1, 2, 3, 4)
        assert space.allocate(1) == (0, 1, 2, 3, 4)
        assert space.allocate(2) == (0, 1, 2, 3, 4)
        assert space.allocate(3) == (0, 1, 2, 3, 4)
        assert space.allocate(4) == (0, 1, 2, 3, 4)
        assert space.allocate(5) == (0, 1, 2, 3, 4)
        assert space.allocate(6) == (0, 1, 2, 3, 4)
        assert space.allocate(7) == (0, 1, 2, 3, 4)
