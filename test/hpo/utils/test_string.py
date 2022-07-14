from textwrap import dedent

import pytest

from ditk.hpo.utils import sblock, rchain


@pytest.mark.unittest
class TestHpoUtilsString:

    def test_sblock(self):
        assert sblock(
            dedent(
                """
            This is first line
            This is 2nd line
            
            This is fourth line.
        """
            ).strip()
        ).strip() == dedent(
            u"""
            1 \u2502 This is first line
            2 \u2502 This is 2nd line
            3 \u2502 
            4 \u2502 This is fourth line.
        """
        ).strip()

    def test_sblock_multiple_lines(self):
        assert sblock(
            dedent(
                """
            This is first line
            This is 2nd line

            This is fourth line.
            a
            b
            c
            d
            e
            f
            g
            h
            i
            j
            k
        """
            ).strip()
        ).strip() == dedent(
            u"""
             1 \u2502 This is first line
             2 \u2502 This is 2nd line
             3 \u2502 
             4 \u2502 This is fourth line.
             5 \u2502 a
             6 \u2502 b
             7 \u2502 c
             8 \u2502 d
             9 \u2502 e
            10 \u2502 f
            11 \u2502 g
            12 \u2502 h
            13 \u2502 i
            14 \u2502 j
            15 \u2502 k
        """
        ).strip()

    def test_rchain(self):
        assert rchain([('name', 'str'), ('val', 233), ('float', 233.5)]) == "name: 'str', val: 233, float: 233.5"
