import pytest

from ditk.hpo.utils import rchain


@pytest.mark.unittest
class TestHpoUtilsString:

    def test_rchain(self):
        assert rchain([('name', 'str'), ('val', 233), ('float', 233.5)]) == "name: 'str', val: 233, float: 233.5"
