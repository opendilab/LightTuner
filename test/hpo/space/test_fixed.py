import pytest

from ditk.hpo.space import FixedSpace


@pytest.mark.unittest
class TestHpoSpaceFixed:
    def test_fixed_space(self):
        space = FixedSpace(5)
        assert space.length == 5
        assert space.count == 5
