import pytest
from easydict import EasyDict

from ditk.hpo import R


@pytest.mark.unittest
class TestHpoAlgorithmResult:
    def test_common(self):
        r = R
        assert r(1) == 1
        assert r({'a': 1}) == {'a': 1}
        assert r([1, 2]) == [1, 2]
        assert r(None) is None

    def test_getitem(self):
        r = R['a']
        assert r({'a': 1}) == 1
        assert r({'a': 2, 'b': 1}) == 2

        r = R[1]
        assert r([1, 2]) == 2
        assert r([2, 3, 5, 7]) == 3

    def test_getattr(self):
        r = R.a
        assert r(EasyDict({'a': 1})) == 1
        assert r(EasyDict({'a': 2, 'b': 1})) == 2
        with pytest.raises(AttributeError):
            r({'a': 1})

    def test_is_(self):
        r = R.is_(None)
        assert r(None) is True
        assert r(1) is False

    def test_isinstance(self):
        r = R.isinstance_(int)
        assert r(1)
        assert not r(1.0)
        assert not r('a')

    def test_abs(self):
        r = R.abs()
        assert r(-1) == 1
        assert r(-0.5) == pytest.approx(0.5)
        assert r(0) == 0

    def test_len(self):
        r = R.len()
        assert r([1, 2]) == 2
        assert r([]) == 0
        assert r('abcdefg') == 7

    def test_eq(self):
        r = R == 1
        assert not r(2)
        assert r(1)
        assert not r(0)

    def test_ne(self):
        r = R != 1
        assert r(2)
        assert not r(1)
        assert r(0)

    def test_gt(self):
        r = R > 1
        assert r(2)
        assert not r(1)
        assert not r(0)

    def test_ge(self):
        r = R >= 1
        assert r(2)
        assert r(1)
        assert not r(0)

    def test_lt(self):
        r = R < 1
        assert not r(2)
        assert not r(1)
        assert r(0)

    def test_le(self):
        r = R <= 1
        assert not r(2)
        assert r(1)
        assert r(0)

    def test_and(self):
        r = (R['a'] > 1) & (R['b'] > 2)
        assert r({'a': 2, 'b': 3})
        assert not r({'a': 2, 'b': 2})
        assert not r({'a': 1, 'b': 2})

        r = True & (R['a'] > 1)
        assert r({'a': 2})
        assert not r({'a': 1})

        r = False & (R['a'] > 1)
        assert not r({'a': 2})
        assert not r({'a': 1})

    def test_or(self):
        r = (R['a'] > 1) | (R['b'] > 2)
        assert r({'a': 2, 'b': 3})
        assert r({'a': 2, 'b': 2})
        assert not r({'a': 1, 'b': 2})

        r = True | (R['a'] > 1)
        assert r({'a': 2})
        assert r({'a': 1})

        r = False | (R['a'] > 1)
        assert r({'a': 2})
        assert not r({'a': 1})

    def test_inv(self):
        r = ~(R['a'] > 1) & (R['b'] > 2)
        assert not r({'a': 2, 'b': 3})
        assert not r({'a': 2, 'b': 2})
        assert r({'a': 1, 'b': 3})
        assert not r({'a': 1, 'b': 2})

    def test_or_func(self):
        def _b_check(x):
            return x['b'] > 2

        r = (R['a'] > 1) | _b_check
        assert r({'a': 2, 'b': 3})
        assert r({'a': 2, 'b': 2})
        assert not r({'a': 1, 'b': 2})
