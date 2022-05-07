import logging
import os
import pathlib
import sys
from unittest import mock

import pytest
from rich.logging import RichHandler
from testfixtures import LogCapture, OutputCapture

from ditk.logging import get_logger, TerminalHandler
from ..testing import ansi_unescape, tempdir


@pytest.mark.unittest
class TestLoggingLog:
    def test_simple_rich(self):
        with LogCapture() as log, OutputCapture(separate=True) as output:
            logger = get_logger()
            assert logger.name == 'root'

            logger.info('This is info.')
            logger.warning('This is warning.')
            logger.error('This is error.')
            logger.critical('This is critical.')

        log.check(
            ('root', 'INFO', 'This is info.'),
            ('root', 'WARNING', 'This is warning.'),
            ('root', 'ERROR', 'This is error.'),
            ('root', 'CRITICAL', 'This is critical.')
        )

        stdout, stderr = ansi_unescape(output.stdout.getvalue()), ansi_unescape(output.stderr.getvalue())
        assert stdout.strip() == ''
        assert 'INFO     This is info.' in stderr
        assert 'WARNING  This is warning.' in stderr
        assert 'ERROR    This is error.' in stderr
        assert 'CRITICAL This is critical.' in stderr

    def test_stream(self):
        logger = get_logger('stream_test')
        assert logger.name == 'stream_test'

        with LogCapture() as log, OutputCapture(separate=True) as output:
            with mock.patch.dict(os.environ, {'DISABLE_RICH': '1'}):
                logger.info('This is info.')
                logger.warning('This is warning.')
            with mock.patch.dict(os.environ, {'DISABLE_RICH': ''}):
                logger.error('This is error.')
                logger.critical('This is critical.')

        log.check(
            ('stream_test', 'INFO', 'This is info.'),
            ('stream_test', 'WARNING', 'This is warning.'),
            ('stream_test', 'ERROR', 'This is error.'),
            ('stream_test', 'CRITICAL', 'This is critical.')
        )

        stdout, stderr = ansi_unescape(output.stdout.getvalue()), ansi_unescape(output.stderr.getvalue())
        assert '[INFO] This is info.' in stderr
        assert '[WARNING] This is warning.' in stderr
        assert 'ERROR    This is error.' in stderr
        assert 'CRITICAL This is critical.' in stderr

    def test_with_basic_stream(self):
        with LogCapture() as log, OutputCapture(separate=True) as output:
            bl = logging.getLogger('basics_stream')
            hdl = logging.StreamHandler(sys.stdout)
            hdl.setFormatter(logging.Formatter(
                fmt='[%(asctime)s][%(filename)s:%(lineno)d][THIS IS UNITTEST][%(levelname)s] %(message)s',
                datefmt="%m-%d %H:%M:%S",
            ))
            bl.addHandler(hdl)

            logger = get_logger('basics_stream')
            assert logger.name == 'basics_stream'

            logger.info('This is info.')
            logger.warning('This is warning.')
            logger.error('This is error.')
            logger.critical('This is critical.')

        log.check(
            ('basics_stream',
             'WARNING',
             'Because a terminal handler is detected in the global configuration, no more '
             'terminal handlers will be added, and the original will be preserved to '
             'avoid any conflicts.'),
            ('basics_stream', 'INFO', 'This is info.'),
            ('basics_stream', 'WARNING', 'This is warning.'),
            ('basics_stream', 'ERROR', 'This is error.'),
            ('basics_stream', 'CRITICAL', 'This is critical.')
        )

        stdout, stderr = ansi_unescape(output.stdout.getvalue()), ansi_unescape(output.stderr.getvalue())
        assert 'the original will be preserved to avoid any conflicts.' in stdout
        assert '[THIS IS UNITTEST][INFO] This is info.' in stdout
        assert '[THIS IS UNITTEST][WARNING] This is warning.' in stdout
        assert '[THIS IS UNITTEST][ERROR] This is error.' in stdout
        assert '[THIS IS UNITTEST][CRITICAL] This is critical.' in stdout

        assert stderr.strip() == ''

    def test_with_basic_rich(self):
        with LogCapture() as log, OutputCapture(separate=True) as output:
            bl = logging.getLogger('basics_rich')

            hdl = RichHandler()
            hdl.setFormatter(logging.Formatter(
                fmt='[THIS IS UNITTEST] %(message)s',
                datefmt="%m-%d %H:%M:%S",
            ))
            bl.addHandler(hdl)

            logger = get_logger('basics_rich')
            assert logger.name == 'basics_rich'

            logger.info('This is info.')
            logger.warning('This is warning.')
            logger.error('This is error.')
            logger.critical('This is critical.')

        log.check(
            ('basics_rich',
             'WARNING',
             'Because a terminal handler is detected in the global configuration, no more '
             'terminal handlers will be added, and the original will be preserved to '
             'avoid any conflicts.'),
            ('basics_rich', 'INFO', 'This is info.'),
            ('basics_rich', 'WARNING', 'This is warning.'),
            ('basics_rich', 'ERROR', 'This is error.'),
            ('basics_rich', 'CRITICAL', 'This is critical.')
        )

        stdout, stderr = ansi_unescape(output.stdout.getvalue()), ansi_unescape(output.stderr.getvalue())

        assert 'WARNING  [THIS IS UNITTEST] Because a terminal handler' in stdout
        assert 'INFO     [THIS IS UNITTEST] This is info.' in stdout
        assert 'WARNING  [THIS IS UNITTEST] This is warning.' in stdout
        assert 'ERROR    [THIS IS UNITTEST] This is error.' in stdout
        assert 'CRITICAL [THIS IS UNITTEST] This is critical.' in stdout

        assert stderr.strip() == ''

    def test_with_basic_terminal(self):
        with LogCapture() as log, OutputCapture(separate=True) as output:
            bl = logging.getLogger('basics_terminal')
            hdl = TerminalHandler(use_stdout=True)
            hdl.setFormatter(logging.Formatter(
                fmt='[THIS IS UNITTEST] %(message)s',
                datefmt="%m-%d %H:%M:%S",
            ))
            bl.addHandler(hdl)

            logger = get_logger('basics_terminal')
            assert logger.name == 'basics_terminal'

            logger.info('This is info.')
            logger.warning('This is warning.')
            logger.error('This is error.')
            logger.critical('This is critical.')

        log.check(
            ('basics_terminal',
             'WARNING',
             'Because a terminal handler is detected in the global configuration, no more '
             'terminal handlers will be added, and the original will be preserved to '
             'avoid any conflicts.'),
            ('basics_terminal', 'INFO', 'This is info.'),
            ('basics_terminal', 'WARNING', 'This is warning.'),
            ('basics_terminal', 'ERROR', 'This is error.'),
            ('basics_terminal', 'CRITICAL', 'This is critical.')
        )

        stdout, stderr = ansi_unescape(output.stdout.getvalue()), ansi_unescape(output.stderr.getvalue())

        assert 'WARNING  Because a terminal handler' in stdout
        assert 'INFO     This is info.' in stdout
        assert 'WARNING  This is warning.' in stdout
        assert 'ERROR    This is error.' in stdout
        assert 'CRITICAL This is critical.' in stdout

        assert stderr.strip() == ''

    def test_with_duplicate(self):
        with LogCapture() as log, OutputCapture(separate=True) as output:
            _ = get_logger('duplicate')

            logger = get_logger('duplicate', with_files=['log_file_1.txt'], use_stdout=True)
            assert logger.name == 'duplicate'

            logger.info('This is info.')
            logger.warning('This is warning.')
            logger.error('This is error.')
            logger.critical('This is critical.')

        log.check(
            ('duplicate',
             'WARNING',
             "Logger 'duplicate' has already exist, extra arguments (with_files: "
             "['log_file_1.txt'], level: None) will be ignored."),
            ('duplicate', 'INFO', 'This is info.'),
            ('duplicate', 'WARNING', 'This is warning.'),
            ('duplicate', 'ERROR', 'This is error.'),
            ('duplicate', 'CRITICAL', 'This is critical.')
        )

        stdout, stderr = ansi_unescape(output.stdout.getvalue()), ansi_unescape(output.stderr.getvalue())
        assert stdout.strip() == ''

        assert 'WARNING  Logger \'duplicate\' has already' in stderr
        assert 'INFO     This is info.' in stderr
        assert 'WARNING  This is warning.' in stderr
        assert 'ERROR    This is error.' in stderr
        assert 'CRITICAL This is critical.' in stderr

    def test_with_files(self):
        with tempdir():
            with LogCapture() as log, OutputCapture(separate=True) as output:
                logger = get_logger('with_files', with_files=['log_file_1.txt', 'log_file_2.txt'])
                assert logger.name == 'with_files'

                logger.info('This is info.')
                logger.warning('This is warning.')
                logger.error('This is error.')
                logger.critical('This is critical.')

            log.check(
                ('with_files', 'INFO', 'This is info.'),
                ('with_files', 'WARNING', 'This is warning.'),
                ('with_files', 'ERROR', 'This is error.'),
                ('with_files', 'CRITICAL', 'This is critical.')
            )

            stdout, stderr = ansi_unescape(output.stdout.getvalue()), ansi_unescape(output.stderr.getvalue())
            assert stdout.strip() == ''
            assert 'INFO     This is info.' in stderr
            assert 'WARNING  This is warning.' in stderr
            assert 'ERROR    This is error.' in stderr
            assert 'CRITICAL This is critical.' in stderr

            log_file_1 = pathlib.Path('log_file_1.txt').read_text()
            assert '[INFO] This is info.' in log_file_1
            assert '[WARNING] This is warning.' in log_file_1
            assert '[ERROR] This is error.' in log_file_1
            assert '[CRITICAL] This is critical.' in log_file_1

            log_file_2 = pathlib.Path('log_file_2.txt').read_text()
            assert '[INFO] This is info.' in log_file_2
            assert '[WARNING] This is warning.' in log_file_2
            assert '[ERROR] This is error.' in log_file_2
            assert '[CRITICAL] This is critical.' in log_file_2
