import io
import os
import textwrap

import pytest

from ditk.hpo.utils import RankList


def _strip(s: str) -> str:
    with io.StringIO(textwrap.dedent(s).strip()) as sf:
        return os.linesep.join(map(str.rstrip, sf))


# noinspection DuplicatedCode
@pytest.mark.unittest
class TestHpoUtilsRanking:
    def test_init_empty(self):
        r = RankList(
            capacity=5,
            columns=[
                ('id', lambda x: x[0]),
                ('name', lambda x: x[1]),
                ('score', lambda x: x[2]),
            ],
            key=lambda x: x[2],
            reverse=True,
        )

        assert len(r) == 0

    def test_init_common(self):
        r = RankList(
            capacity=5,
            columns=[
                ('id', lambda x: x[0]),
                ('name', lambda x: x[1]),
                ('score', lambda x: x[2]),
            ],
            init=[
                (1, 'hansbug', 90),
                (2, 'hansbug', 90),
                (-9, 'hansbug', 99),
            ],
            key=lambda x: x[2],
            reverse=True,
        )

        assert len(r) == 3
        assert list(r) == [
            (-9, 'hansbug', 99),
            (1, 'hansbug', 90),
            (2, 'hansbug', 90),
        ]

    def test_actual_use(self):
        r = RankList(
            capacity=5,
            columns=[
                ('id', lambda x: x[0]),
                ('name', lambda x: x[1]),
                ('score', lambda x: x[2]),
            ],
            init=[
                (-9, 'hansbug', 99)
            ],
            key=lambda x: x[2],
            reverse=True,
        )

        assert len(r) == 1
        assert r[0] == (-9, 'hansbug', 99)
        assert r[-1] == (-9, 'hansbug', 99)
        assert list(r) == [
            (-9, 'hansbug', 99),
        ]
        assert _strip(str(r)) == _strip("""
+------+---------+---------+
|   id | name    |   score |
|------+---------+---------|
|   -9 | hansbug |      99 |
+------+---------+---------+
        """)

        r.append((1, 'hansbug', 90))
        r.append((2, 'nyz', 95))
        r.append((3, 'hahaha', 80))
        r.append((4, 'hhh', 90))

        assert len(r) == 5
        assert r[0] == (-9, 'hansbug', 99)
        assert r[-1] == (3, 'hahaha', 80)
        assert list(r) == [
            (-9, 'hansbug', 99),
            (2, 'nyz', 95),
            (1, 'hansbug', 90),
            (4, 'hhh', 90),
            (3, 'hahaha', 80),
        ]
        assert _strip(str(r)) == _strip("""
+------+---------+---------+
|   id | name    |   score |
|------+---------+---------|
|   -9 | hansbug |      99 |
|    2 | nyz     |      95 |
|    1 | hansbug |      90 |
|    4 | hhh     |      90 |
|    3 | hahaha  |      80 |
+------+---------+---------+
        """)

        r.append((1, 'hansbug', 90))
        r.append((2, 'nyz', 95))
        r.append((3, 'hahaha', 80))
        r.append((4, 'hhh', 90))

        assert len(r) == 5
        assert r[0] == (-9, 'hansbug', 99)
        assert r[-1] == (4, 'hhh', 90)
        assert list(r) == [
            (-9, 'hansbug', 99),
            (2, 'nyz', 95),
            (2, 'nyz', 95),
            (1, 'hansbug', 90),
            (4, 'hhh', 90),
        ]
        assert _strip(str(r)) == _strip("""
+------+---------+---------+
|   id | name    |   score |
|------+---------+---------|
|   -9 | hansbug |      99 |
|    2 | nyz     |      95 |
|    2 | nyz     |      95 |
|    1 | hansbug |      90 |
|    4 | hhh     |      90 |
+------+---------+---------+
        """)
