import logging
import os
import pathlib
import sys
from unittest import mock

import pytest
from hbutils.testing import capture_output, isolated_directory
from rich.logging import RichHandler
from testfixtures import LogCapture

from ditk.logging import get_logger, LoggingTerminalHandler


@pytest.mark.unittest
class TestLoggingLog:
    def test_simple_rich(self):
        with LogCapture() as log, capture_output() as output:
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

        stdout, stderr = output.stdout, output.stderr
        assert stdout.strip() == ''
        assert 'INFO     This is info.' in stderr
        assert 'WARNING  This is warning.' in stderr
        assert 'ERROR    This is error.' in stderr
        assert 'CRITICAL This is critical.' in stderr

    def test_stream(self):
        logger = get_logger('stream_test')
        assert logger.name == 'stream_test'

        with LogCapture() as log, capture_output() as output:
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

        stdout, stderr = output.stdout, output.stderr
        assert '[INFO] This is info.' in stderr
        assert '[WARNING] This is warning.' in stderr
        assert 'ERROR    This is error.' in stderr
        assert 'CRITICAL This is critical.' in stderr

    def test_with_basic_stream(self):
        with LogCapture() as log, capture_output() as output:
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
             'Because a terminal handler is detected in <Logger basics_stream (Level 1)>, no more '
             'terminal handlers will be added, and the original will be preserved to '
             'avoid any conflicts.'),
            ('basics_stream', 'INFO', 'This is info.'),
            ('basics_stream', 'WARNING', 'This is warning.'),
            ('basics_stream', 'ERROR', 'This is error.'),
            ('basics_stream', 'CRITICAL', 'This is critical.')
        )

        stdout, stderr = output.stdout, output.stderr
        assert 'the original will be preserved to avoid any conflicts.' in stdout
        assert '[THIS IS UNITTEST][INFO] This is info.' in stdout
        assert '[THIS IS UNITTEST][WARNING] This is warning.' in stdout
        assert '[THIS IS UNITTEST][ERROR] This is error.' in stdout
        assert '[THIS IS UNITTEST][CRITICAL] This is critical.' in stdout

        assert stderr.strip() == ''

    def test_with_basic_rich(self):
        with LogCapture() as log, capture_output() as output:
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
             'Because a terminal handler is detected in <Logger basics_rich (Level 1)>, no more '
             'terminal handlers will be added, and the original will be preserved to '
             'avoid any conflicts.'),
            ('basics_rich', 'INFO', 'This is info.'),
            ('basics_rich', 'WARNING', 'This is warning.'),
            ('basics_rich', 'ERROR', 'This is error.'),
            ('basics_rich', 'CRITICAL', 'This is critical.')
        )

        stdout, stderr = output.stdout, output.stderr

        assert 'WARNING  [THIS IS UNITTEST] Because a terminal handler' in stdout
        assert 'INFO     [THIS IS UNITTEST] This is info.' in stdout
        assert 'WARNING  [THIS IS UNITTEST] This is warning.' in stdout
        assert 'ERROR    [THIS IS UNITTEST] This is error.' in stdout
        assert 'CRITICAL [THIS IS UNITTEST] This is critical.' in stdout

        assert stderr.strip() == ''

    def test_with_basic_terminal(self):
        with LogCapture() as log, capture_output() as output:
            bl = logging.getLogger('basics_terminal')
            hdl = LoggingTerminalHandler(use_stdout=True)
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
            ('basics_terminal', 'WARNING',
             'Because a terminal handler is detected in <Logger basics_terminal (Level 1)>, no more '
             'terminal handlers will be added, and the original will be preserved to '
             'avoid any conflicts.'),
            ('basics_terminal', 'INFO', 'This is info.'),
            ('basics_terminal', 'WARNING', 'This is warning.'),
            ('basics_terminal', 'ERROR', 'This is error.'),
            ('basics_terminal', 'CRITICAL', 'This is critical.')
        )

        stdout, stderr = output.stdout, output.stderr

        assert 'WARNING  Because a terminal handler' in stdout
        assert 'INFO     This is info.' in stdout
        assert 'WARNING  This is warning.' in stdout
        assert 'ERROR    This is error.' in stdout
        assert 'CRITICAL This is critical.' in stdout

        assert stderr.strip() == ''

    def test_with_duplicate(self):
        with isolated_directory():
            with LogCapture() as log, capture_output() as output:
                _ = get_logger('duplicate')

                logger = get_logger('duplicate', with_files=['log_file_1.txt'], use_stdout=True)
                assert logger.name == 'duplicate'

                logger.info('This is info.')
                logger.warning('This is warning.')
                logger.error('This is error.')
                logger.critical('This is critical.')

            log.check(
                ('duplicate', 'WARNING',
                 'Because a terminal handler is detected in <Logger duplicate (Level 1)>, no more '
                 'terminal handlers will be added, and the original will be preserved to '
                 'avoid any conflicts.'),
                ('duplicate', 'WARNING',
                 'The original terminal handler is using sys.stderr, but this will be changed '
                 "to sys.stdout due to the setting of 'use_stdout': True."),
                ('duplicate', 'INFO', 'This is info.'),
                ('duplicate', 'WARNING', 'This is warning.'),
                ('duplicate', 'ERROR', 'This is error.'),
                ('duplicate', 'CRITICAL', 'This is critical.')
            )

            stdout, stderr = output.stdout, output.stderr
            assert 'WARNING  Because a terminal handler is' in stdout
            assert 'WARNING  The original terminal handler' in stdout
            assert 'INFO     This is info.' in stdout
            assert 'WARNING  This is warning.' in stdout
            assert 'ERROR    This is error.' in stdout
            assert 'CRITICAL This is critical.' in stdout

            assert stderr.strip() == ''

            log_file_1 = pathlib.Path('log_file_1.txt').read_text()
            assert '[WARNING] Because a terminal handler is' in log_file_1
            assert '[WARNING] The original terminal handler is' in log_file_1
            assert '[INFO] This is info.' in log_file_1
            assert '[WARNING] This is warning.' in log_file_1
            assert '[ERROR] This is error.' in log_file_1
            assert '[CRITICAL] This is critical.' in log_file_1

    def test_with_files(self):
        with isolated_directory():
            with LogCapture() as log, capture_output() as output:
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

            stdout, stderr = output.stdout, output.stderr
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

    def test_new_level(self):
        _ = get_logger('new_level')

        with LogCapture() as log, capture_output() as output:
            logger = get_logger('new_level', level=logging.WARNING)
            assert logger.name == 'new_level'

            logger.info('This is info.')
            logger.warning('This is warning.')
            logger.error('This is error.')
            logger.critical('This is critical.')

        log.check(
            ('new_level', 'WARNING',
             'Because a terminal handler is detected in <Logger new_level (WARNING)>, no more '
             'terminal handlers will be added, and the original will be preserved to '
             'avoid any conflicts.'),
            ('new_level', 'WARNING', 'This is warning.'),
            ('new_level', 'ERROR', 'This is error.'),
            ('new_level', 'CRITICAL', 'This is critical.')
        )

        stdout, stderr = output.stdout, output.stderr
        assert stdout.strip() == ''
        assert 'WARNING  Because a terminal handler is' in stderr
        assert 'INFO     This is info.' not in stderr
        assert 'WARNING  This is warning.' in stderr
        assert 'ERROR    This is error.' in stderr
        assert 'CRITICAL This is critical.' in stderr

    def test_new_use_stdout(self):
        _ = get_logger('new_use_stdout')

        with LogCapture() as log, capture_output() as output:
            logger = get_logger('new_use_stdout', use_stdout=True)
            assert logger.name == 'new_use_stdout'

            logger.info('This is info.')
            logger.warning('This is warning.')
            logger.error('This is error.')
            logger.critical('This is critical.')

        log.check(
            ('new_use_stdout', 'WARNING',
             'Because a terminal handler is detected in <Logger new_use_stdout (Level 1)>, no more '
             'terminal handlers will be added, and the original will be preserved to '
             'avoid any conflicts.'),
            ('new_use_stdout', 'WARNING',
             'The original terminal handler is using sys.stderr, but this will be changed '
             "to sys.stdout due to the setting of 'use_stdout': True."),
            ('new_use_stdout', 'INFO', 'This is info.'),
            ('new_use_stdout', 'WARNING', 'This is warning.'),
            ('new_use_stdout', 'ERROR', 'This is error.'),
            ('new_use_stdout', 'CRITICAL', 'This is critical.')
        )

        stdout, stderr = output.stdout, output.stderr
        assert 'WARNING  Because a terminal handler is' in stdout
        assert 'INFO     This is info.' in stdout
        assert 'WARNING  This is warning.' in stdout
        assert 'ERROR    This is error.' in stdout
        assert 'CRITICAL This is critical.' in stdout
        assert stderr.strip() == ''

    def test_new_files(self):
        with isolated_directory():
            _ = get_logger('new_files', with_files=['log_file_1.txt', 'log_file_2.txt'])

            with LogCapture() as log, capture_output() as output:
                logger = get_logger('new_files', with_files=['log_file_1.txt', 'log_file_3.txt'])
                assert logger.name == 'new_files'

                logger.info('This is info.')
                logger.warning('This is warning.')
                logger.error('This is error.')
                logger.critical('This is critical.')

            log.check(
                ('new_files', 'WARNING',
                 'Because a terminal handler is detected in <Logger new_files (Level 1)>, no more '
                 'terminal handlers will be added, and the original will be preserved to '
                 'avoid any conflicts.'),
                ('new_files', 'WARNING',
                 "File 'log_file_1.txt' has already been added to this logger, so this "
                 'configuration will be ignored.'),
                ('new_files', 'INFO', 'This is info.'),
                ('new_files', 'WARNING', 'This is warning.'),
                ('new_files', 'ERROR', 'This is error.'),
                ('new_files', 'CRITICAL', 'This is critical.')
            )

            stdout, stderr = output.stdout, output.stderr
            assert stdout.strip() == ''
            assert 'WARNING  Because a terminal handler' in stderr
            assert "WARNING  File 'log_file_1.txt' has" in stderr
            assert 'INFO     This is info.' in stderr
            assert 'WARNING  This is warning.' in stderr
            assert 'ERROR    This is error.' in stderr
            assert 'CRITICAL This is critical.' in stderr

            log_file_1 = pathlib.Path('log_file_1.txt').read_text()
            assert '[WARNING] Because a terminal handler' in log_file_1
            assert "[WARNING] File 'log_file_1.txt' has" in log_file_1
            assert '[INFO] This is info.' in log_file_1
            assert '[WARNING] This is warning.' in log_file_1
            assert '[ERROR] This is error.' in log_file_1
            assert '[CRITICAL] This is critical.' in log_file_1

            log_file_2 = pathlib.Path('log_file_1.txt').read_text()
            assert '[WARNING] Because a terminal handler' in log_file_2
            assert "[WARNING] File 'log_file_1.txt' has" in log_file_2
            assert '[INFO] This is info.' in log_file_2
            assert '[WARNING] This is warning.' in log_file_2
            assert '[ERROR] This is error.' in log_file_2
            assert '[CRITICAL] This is critical.' in log_file_2

            log_file_3 = pathlib.Path('log_file_1.txt').read_text()
            assert '[WARNING] Because a terminal handler' in log_file_3
            assert "[WARNING] File 'log_file_1.txt' has" in log_file_3
            assert '[INFO] This is info.' in log_file_3
            assert '[WARNING] This is warning.' in log_file_3
            assert '[ERROR] This is error.' in log_file_3
            assert '[CRITICAL] This is critical.' in log_file_3
