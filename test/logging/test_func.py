import logging
import os
from unittest import mock

import pytest
from hbutils.testing import capture_output

import ditk.logging
from ..testing import init_handlers


@pytest.mark.unittest
class TestLoggingFunc:

    @init_handlers([])
    def test_loggings(self):
        with capture_output() as o:
            ditk.logging.debug('This is debug.')
            ditk.logging.info('This is info.')
            ditk.logging.warn('This is warn.')
            ditk.logging.warning('This is warning.')
            ditk.logging.error('This is error.')
            with mock.patch.dict(os.environ, {'DISABLE_RICH': '1'}):
                ditk.logging.critical('This is critical.')
                ditk.logging.fatal('This is fatal.')
                ditk.logging.log(logging.WARNING, 'This is warn log.')

                try:
                    raise ValueError('This is value error.')
                except Exception as err:
                    ditk.logging.exception(err)

        assert o.stdout.strip() == ''
        assert 'DEBUG    This is debug.' not in o.stderr
        assert 'INFO     This is info.' not in o.stderr
        assert 'WARNING  This is warn.' in o.stderr
        assert 'WARNING  This is warning.' in o.stderr
        assert 'ERROR    This is error.' in o.stderr
        assert '[CRITICAL] This is critical.' in o.stderr
        assert '[CRITICAL] This is fatal.' in o.stderr
        assert '[WARNING] This is warn log.' in o.stderr
        assert 'ValueError: This is value error.' in o.stderr
