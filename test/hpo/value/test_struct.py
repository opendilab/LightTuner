import pytest

from ditk.hpo import uniform, choice, quniform
from ditk.hpo.value import struct_values


@pytest.mark.unittest
class TestHpoValueStruct:
    def test_struct_values(self):
        s1 = choice(['a', 'b', 'c'])
        s2 = uniform(-10, 20.2)
        s3 = quniform(-20.2, 10, 0.2)
        s4 = uniform(-5, 10.1)
        func, items = struct_values({
            'values': {'a': s2, 'b': (s3, s4), 'e': 12.7},
            'need': s1,
        })
        ns1, ns2, ns3, ns4 = items
        assert ns1 is s1
        assert ns2 is s2
        assert ns3 is s3
        assert ns4 is s4

        rf = func('a', 2.0, 3.5, -4.75)
        assert rf['need'] == 'a'
        assert rf['values']['a'] == pytest.approx(2.0)
        assert rf['values']['b'][0] == pytest.approx(3.5)
        assert rf['values']['b'][1] == pytest.approx(-4.75)
        assert rf['values']['e'] == pytest.approx(12.7)
