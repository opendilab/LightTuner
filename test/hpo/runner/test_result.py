import pytest
from easydict import EasyDict
from hbutils.expression import efunc

from ditk.hpo.runner.result import R, _to_expr, _ResultExpression, _to_callable


@pytest.mark.unittest
class TestHpoAlgorithmResult:

    def test_common(self):
        r = efunc(R)
        assert r(1) == 1
        assert r({'a': 1}) == {'a': 1}
        assert r([1, 2]) == [1, 2]
        assert r(None) is None

    def test_getitem(self):
        r = efunc(R['a'])
        assert r({'a': 1}) == 1
        assert r({'a': 2, 'b': 1}) == 2

        r = efunc(R[1])
        assert r([1, 2]) == 2
        assert r([2, 3, 5, 7]) == 3

    def test_getattr(self):
        r = efunc(R.a)
        assert r(EasyDict({'a': 1})) == 1
        assert r(EasyDict({'a': 2, 'b': 1})) == 2
        with pytest.raises(AttributeError):
            r({'a': 1})

    def test_is_(self):
        r = efunc(R.is_(None))
        assert r(None) is True
        assert r(1) is False

    def test_isinstance(self):
        r = efunc(R.isinstance_(int))
        assert r(1)
        assert not r(1.0)
        assert not r('a')

    def test_abs(self):
        r = efunc(R.abs())
        assert r(-1) == 1
        assert r(-0.5) == pytest.approx(0.5)
        assert r(0) == 0

    def test_len(self):
        r = efunc(R.len())
        assert r([1, 2]) == 2
        assert r([]) == 0
        assert r('abcdefg') == 7

    def test_eq(self):
        r = efunc(R == 1)
        assert not r(2)
        assert r(1)
        assert not r(0)

    def test_ne(self):
        r = efunc(R != 1)
        assert r(2)
        assert not r(1)
        assert r(0)

    def test_gt(self):
        r = efunc(R > 1)
        assert r(2)
        assert not r(1)
        assert not r(0)

    def test_ge(self):
        r = efunc(R >= 1)
        assert r(2)
        assert r(1)
        assert not r(0)

    def test_lt(self):
        r = efunc(R < 1)
        assert not r(2)
        assert not r(1)
        assert r(0)

    def test_le(self):
        r = efunc(R <= 1)
        assert not r(2)
        assert r(1)
        assert r(0)

    def test_and(self):
        r = efunc((R['a'] > 1) & (R['b'] > 2))
        assert r({'a': 2, 'b': 3})
        assert not r({'a': 2, 'b': 2})
        assert not r({'a': 1, 'b': 2})

        r = efunc(True & (R['a'] > 1))
        assert r({'a': 2})
        assert not r({'a': 1})

        r = efunc(False & (R['a'] > 1))
        assert not r({'a': 2})
        assert not r({'a': 1})

    def test_or(self):
        r = efunc((R['a'] > 1) | (R['b'] > 2))
        assert r({'a': 2, 'b': 3})
        assert r({'a': 2, 'b': 2})
        assert not r({'a': 1, 'b': 2})

        r = efunc(True | (R['a'] > 1))
        assert r({'a': 2})
        assert r({'a': 1})

        r = efunc(False | (R['a'] > 1))
        assert r({'a': 2})
        assert not r({'a': 1})

    def test_inv(self):
        r = efunc(~(R['a'] > 1) & (R['b'] > 2))
        assert not r({'a': 2, 'b': 3})
        assert not r({'a': 2, 'b': 2})
        assert r({'a': 1, 'b': 3})
        assert not r({'a': 1, 'b': 2})

    def test_or_func(self):

        def _b_check(x):
            return x['b'] > 2

        r = efunc((R['a'] > 1) | _b_check)
        assert r({'a': 2, 'b': 3})
        assert r({'a': 2, 'b': 2})
        assert not r({'a': 1, 'b': 2})

    def test_sum(self):
        r = efunc(R['a'].sum())
        assert r({'a': [1, 2, 3, 4, 5], 'b': [2, 3, 5, 7]}) == 15
        assert r({'a': [2, 3, 5, 7], 'b': [1, 2, 3, 4, 5]}) == 17

    def test_mean(self):
        r = efunc(R['a'].mean())
        assert r({'a': [1, 2, 3, 4, 5], 'b': [2, 3, 5, 7]}) == pytest.approx(3.0)
        assert r({'a': [2, 3, 5, 7], 'b': [1, 2, 3, 4, 5]}) == pytest.approx(4.25)

    def test_stdev(self):
        r = efunc(R['a'].stdev())
        assert r({'a': [1, 2, 3, 4, 5], 'b': [2, 3, 5, 7]}) == pytest.approx(1.5811388300841898)
        assert r({'a': [2, 3, 5, 7], 'b': [1, 2, 3, 4, 5]}) == pytest.approx(2.217355782608345)

    def test_to_expr(self):
        r1 = R
        assert _to_expr(r1) is r1
        assert efunc(r1)({'a': 1}) == {'a': 1}

        r2 = R['a']
        assert _to_expr(r2) is r2
        assert efunc(r2)({'a': 1}) == 1

        def r3(x):
            return x + 1

        assert isinstance(_to_expr(r3), _ResultExpression)
        assert efunc(_to_expr(r3))(1) == 2

        r4 = 233
        assert isinstance(_to_expr(r4), _ResultExpression)
        assert efunc(_to_expr(r4))(1) == 233

    def test_to_callable(self):
        r1 = R
        assert callable(_to_callable(r1))
        assert _to_callable(r1)({'a': 1}) == {'a': 1}

        r2 = R['a']
        assert callable(_to_callable(r2))
        assert _to_callable(r2)({'a': 1}) == 1

        def r3(x):
            return x + 1

        assert callable(_to_callable(r3))
        assert _to_callable(r3)(1) == 2

        r4 = 233
        assert callable(_to_callable(r4))
        assert _to_callable(r4)(1) == 233
