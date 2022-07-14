import pytest

from ditk.hpo.utils import is_function


@pytest.mark.unittest
class TestHpoUtilsType:

    def test_is_function(self):
        assert is_function(lambda: None)
        assert is_function(max)
        assert is_function(len)
        assert is_function([].append)
        assert is_function(object.__init__)
        assert is_function(object().__str__)
        assert is_function(str.join)
        assert is_function(dict.__dict__['fromkeys'])

        assert not is_function(type)
        assert not is_function(int)
        assert not is_function(1)
        assert not is_function(None)
