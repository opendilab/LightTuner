import pytest

from ditk.hpo import choice
from ditk.hpo.algorithm.bayes import hyper_to_bound
from ditk.hpo.space import ContinuousSpace, SeparateSpace
from ditk.hpo.value import HyperValue


# noinspection DuplicatedCode
@pytest.mark.unittest
class TestHpoAlgorithmBayesAlgorithm:
    def test_hyper_to_bound(self):
        hv1 = HyperValue(ContinuousSpace(0.4, 2.2))
        (lbound, ubound), func = hyper_to_bound(hv1)
        assert lbound == pytest.approx(0.4)
        assert ubound == pytest.approx(2.2)
        assert func(1) == 1
        assert func(2.2) == pytest.approx(2.2)
        assert func(290384.92387) == pytest.approx(290384.92387)

        hv2 = 2 ** (hv1 + 2)
        (lbound, ubound), func = hyper_to_bound(hv2)
        assert lbound == pytest.approx(0.4)
        assert ubound == pytest.approx(2.2)
        assert func(1) == 8
        assert func(2.2) == pytest.approx(18.37917367995256)
        assert func(4.92387) == pytest.approx(121.42065073539287)

        hv3 = HyperValue(SeparateSpace(10.2, 12.4, 0.2))
        (lbound, ubound), func = hyper_to_bound(hv3)
        assert lbound == pytest.approx(0.0)
        assert ubound == pytest.approx(12.0)
        assert func(1) == pytest.approx(10.4)
        assert func(2.2) == pytest.approx(10.6)
        assert func(4.92387) == pytest.approx(11.0)
        assert func(12.0) == pytest.approx(12.4)

        hv4 = 2 ** (hv3 + 1)
        (lbound, ubound), func = hyper_to_bound(hv4)
        assert lbound == pytest.approx(0.0)
        assert ubound == pytest.approx(12.0)
        assert func(1) == pytest.approx(2702.3522012628846)
        assert func(2.2) == pytest.approx(3104.1875282132946)
        assert func(4.92387) == pytest.approx(4096.0)
        assert func(12.0) == pytest.approx(10809.408805051538)

        hv5 = choice(['a', 'b', 'c'])
        with pytest.raises(TypeError):
            hyper_to_bound(hv5)
