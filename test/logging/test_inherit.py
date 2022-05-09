import logging

import pytest

import ditk.logging

_CHANGED = [
    'critical', 'fatal', 'error', 'exception',
    'warning', 'warn', 'info', 'debug', 'log',
    'getLogger',
]


@pytest.mark.unittest
class TestLoggingInherit:
    @pytest.mark.parametrize('name', [name for name in logging.__all__ if name not in _CHANGED])
    def test_inherit(self, name):
        assert getattr(ditk.logging, name) is getattr(logging, name)
