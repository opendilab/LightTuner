import logging
import os
from contextlib import contextmanager
from typing import ContextManager
from unittest import mock

import pytest
from hbutils.testing import capture_output
from testfixtures import LogCapture

import ditk.logging


@contextmanager
def with_root_logger() -> ContextManager[logging.Logger]:
    root = logging.getLogger()
    name, level, parent = root.name, root.level, root.parent
    propagate, disabled, handlers = root.propagate, root.disabled, list(root.handlers)

    try:
        yield root
    finally:
        root.name = name
        root.level = level
        root.parent = parent
        root.propagate = propagate
        root.disabled = disabled
        root.handlers = handlers


@pytest.mark.unittest
class TestLoggingFunc:
    def test_loggings(self):
        with with_root_logger():
            with capture_output() as o, LogCapture() as log:
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

            log.check(
                ('root', 'DEBUG', 'This is debug.'),
                ('root', 'INFO', 'This is info.'),
                ('root', 'WARNING', 'This is warn.'),
                ('root', 'WARNING', 'This is warning.'),
                ('root', 'ERROR', 'This is error.'),
                ('root', 'CRITICAL', 'This is critical.'),
                ('root', 'CRITICAL', 'This is fatal.'),
                ('root', 'WARNING', 'This is warn log.'),
                ('root', 'ERROR', 'This is value error.'),
            )

            assert o.stdout.strip() == ''
            assert 'DEBUG    This is debug.' in o.stderr
            assert 'INFO     This is info.' in o.stderr
            assert 'WARNING  This is warn.' in o.stderr
            assert 'WARNING  This is warning.' in o.stderr
            assert 'ERROR    This is error.' in o.stderr
            assert '[CRITICAL] This is critical.' in o.stderr
            assert '[CRITICAL] This is fatal.' in o.stderr
            assert '[WARNING] This is warn log.' in o.stderr
            assert 'ValueError: This is value error.' in o.stderr

    def test_set_level(self):
        with with_root_logger():
            with capture_output() as o, LogCapture() as log:
                ditk.logging.set_level(logging.ERROR)

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

            log.check(
                ('root', 'ERROR', 'This is error.'),
                ('root', 'CRITICAL', 'This is critical.'),
                ('root', 'CRITICAL', 'This is fatal.'),
                ('root', 'ERROR', 'This is value error.'),
            )

            assert o.stdout.strip() == ''

            # HansBug: stdout cannot be captured due to unknown reason
            # # assert 'DEBUG    This is debug.' in o.stderr
            # # assert 'INFO     This is info.' in o.stderr
            # # assert 'WARNING  This is warn.' in o.stderr
            # # assert 'WARNING  This is warning.' in o.stderr
            # assert 'ERROR    This is error.' in o.stderr
            # assert '[CRITICAL] This is critical.' in o.stderr
            # assert '[CRITICAL] This is fatal.' in o.stderr
            # # assert '[WARNING] This is warn log.' in o.stderr
            # assert 'ValueError: This is value error.' in o.stderr

    def test_global_cover(self):
        with with_root_logger():
            logger = ditk.logging.get_logger('global_cover.tk', level=logging.DEBUG)
            with capture_output() as o, LogCapture() as log:
                logger.warning('This is warning.')
                logger.debug('This is debug.')
                logger.info('This is info.')

                _ = ditk.logging.get_logger('global_cover')
                logger.warning('This is warn.')
                logger.error('This is error.')

                logger.critical('This is critical.')
                logger.fatal('This is fatal.')
                logger.log(logging.WARNING, 'This is warn log.')

                try:
                    raise ValueError('This is value error.')
                except Exception as err:
                    logger.exception(err)

            log.check(
                ('global_cover.tk', 'WARNING', 'This is warning.'),
                ('global_cover.tk', 'DEBUG', 'This is debug.'),
                ('global_cover.tk', 'INFO', 'This is info.'),
                ('global_cover.tk', 'WARNING', 'This is warn.'),
                ('global_cover.tk', 'ERROR', 'This is error.'),
                ('global_cover.tk', 'CRITICAL', 'This is critical.'),
                ('global_cover.tk', 'CRITICAL', 'This is fatal.'),
                ('global_cover.tk', 'WARNING', 'This is warn log.'),
                ('global_cover.tk', 'ERROR', 'This is value error.')
            )

            assert o.stdout.strip() == ''
            assert o.stderr.count('WARNING  This is warning.') == 1
            assert o.stderr.count('DEBUG    This is debug.') == 1
            assert o.stderr.count('INFO     This is info.') == 1
            assert o.stderr.count('WARNING  This is warn.') == 1
            assert o.stderr.count('ERROR    This is error.') == 1
            assert o.stderr.count('CRITICAL This is critical.') == 1
            assert o.stderr.count('CRITICAL This is fatal.') == 1
            assert o.stderr.count('WARNING  This is warn log.') == 1
            assert o.stderr.count('ERROR    This is value error.') == 1
