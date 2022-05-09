import logging
import os
import pathlib
import sys
from unittest import mock

import pytest
from hbutils.testing import capture_output, isolated_directory
from rich.logging import RichHandler

from ditk.logging import getLogger, try_init_root
from ..testing import init_handlers


@pytest.mark.unittest
class TestLoggingLog:
    @init_handlers([])
    def test_simple_rich(self):
        try_init_root(logging.DEBUG)
        with capture_output() as output:
            logger = getLogger()
            assert logger.name == 'root'

            logger.info('This is info.')
            logger.warning('This is warning.')
            logger.error('This is error.')
            logger.critical('This is critical.')

        stdout, stderr = output.stdout, output.stderr
        assert stdout.strip() == ''
        assert 'INFO     This is info.' in stderr
        assert 'WARNING  This is warning.' in stderr
        assert 'ERROR    This is error.' in stderr
        assert 'CRITICAL This is critical.' in stderr

    @init_handlers([])
    def test_stream(self):
        try_init_root(logging.DEBUG)
        with capture_output() as output:
            logger = getLogger('stream_test')
            assert logger.name == 'stream_test'

            with mock.patch.dict(os.environ, {'DISABLE_RICH': '1'}):
                logger.info('This is info.')
                logger.warning('This is warning.')
            with mock.patch.dict(os.environ, {'DISABLE_RICH': ''}):
                logger.error('This is error.')
                logger.critical('This is critical.')

        stdout, stderr = output.stdout, output.stderr
        assert '[INFO] This is info.' in stderr
        assert '[WARNING] This is warning.' in stderr
        assert 'ERROR    This is error.' in stderr
        assert 'CRITICAL This is critical.' in stderr

    @init_handlers([])
    def test_with_basic_stream(self):
        with capture_output() as output:
            root = logging.getLogger()
            root.setLevel(logging.DEBUG)
            hdl = logging.StreamHandler(sys.stdout)
            hdl.setFormatter(logging.Formatter(
                fmt='[%(asctime)s][%(filename)s:%(lineno)d][THIS IS UNITTEST][%(levelname)s] %(message)s',
                datefmt="%m-%d %H:%M:%S",
            ))
            root.addHandler(hdl)

            logger = getLogger('basics_stream')
            assert logger.name == 'basics_stream'

            logger.info('This is info.')
            logger.warning('This is warning.')
            logger.error('This is error.')
            logger.critical('This is critical.')

        stdout, stderr = output.stdout, output.stderr
        assert stderr.strip() == ''
        assert '[THIS IS UNITTEST][INFO] This is info.' in stdout
        assert '[THIS IS UNITTEST][WARNING] This is warning.' in stdout
        assert '[THIS IS UNITTEST][ERROR] This is error.' in stdout
        assert '[THIS IS UNITTEST][CRITICAL] This is critical.' in stdout

    @init_handlers([])
    def test_with_basic_rich(self):
        try_init_root(logging.DEBUG)
        with capture_output() as output:
            root = logging.getLogger()
            root.setLevel(logging.DEBUG)
            hdl = RichHandler()
            hdl.setFormatter(logging.Formatter(
                fmt='[THIS IS UNITTEST] %(message)s',
                datefmt="%m-%d %H:%M:%S",
            ))
            root.addHandler(hdl)

            logger = getLogger('basics_rich')
            assert logger.name == 'basics_rich'

            logger.info('This is info.')
            logger.warning('This is warning.')
            logger.error('This is error.')
            logger.critical('This is critical.')

        stdout, stderr = output.stdout, output.stderr

        assert 'INFO     [THIS IS UNITTEST] This is info.' in stdout
        assert 'WARNING  [THIS IS UNITTEST] This is warning.' in stdout
        assert 'ERROR    [THIS IS UNITTEST] This is error.' in stdout
        assert 'CRITICAL [THIS IS UNITTEST] This is critical.' in stdout

        assert 'INFO     This is info.' in stderr
        assert 'WARNING  This is warning.' in stderr
        assert 'ERROR    This is error.' in stderr
        assert 'CRITICAL This is critical.' in stderr

    @init_handlers([])
    def test_with_files(self):
        try_init_root(logging.DEBUG)
        with isolated_directory():
            with capture_output() as output:
                logger = getLogger('with_files', with_files=['log_file_1.txt', 'log_file_2.txt'])
                assert logger.name == 'with_files'

                logger.info('This is info.')
                logger.warning('This is warning.')
                logger.error('This is error.')
                logger.critical('This is critical.')

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

    @init_handlers([])
    def test_new_level(self):
        try_init_root(logging.DEBUG)
        with capture_output() as output:
            _ = getLogger('new_level')

            logger = getLogger('new_level', level=logging.WARNING)
            assert logger.name == 'new_level'

            logger.info('This is info.')
            logger.warning('This is warning.')
            logger.error('This is error.')
            logger.critical('This is critical.')

        stdout, stderr = output.stdout, output.stderr
        assert stdout.strip() == ''
        assert 'INFO     This is info.' not in stderr
        assert 'WARNING  This is warning.' in stderr
        assert 'ERROR    This is error.' in stderr
        assert 'CRITICAL This is critical.' in stderr

    @init_handlers([])
    def test_new_files(self):
        try_init_root(logging.DEBUG)
        with isolated_directory():
            with capture_output() as output:
                _ = getLogger('new_files', with_files=['log_file_1.txt', 'log_file_2.txt'])
                logger = getLogger('new_files', with_files=['log_file_1.txt', 'log_file_3.txt'])
                assert logger.name == 'new_files'

                logger.info('This is info.')
                logger.warning('This is warning.')
                logger.error('This is error.')
                logger.critical('This is critical.')

            stdout, stderr = output.stdout, output.stderr
            assert stdout.strip() == ''
            assert "WARNING  File 'log_file_1.txt' has" in stderr
            assert 'INFO     This is info.' in stderr
            assert 'WARNING  This is warning.' in stderr
            assert 'ERROR    This is error.' in stderr
            assert 'CRITICAL This is critical.' in stderr

            log_file_1 = pathlib.Path('log_file_1.txt').read_text()
            assert "[WARNING] File 'log_file_1.txt' has" in log_file_1
            assert '[INFO] This is info.' in log_file_1
            assert '[WARNING] This is warning.' in log_file_1
            assert '[ERROR] This is error.' in log_file_1
            assert '[CRITICAL] This is critical.' in log_file_1

            log_file_2 = pathlib.Path('log_file_1.txt').read_text()
            assert "[WARNING] File 'log_file_1.txt' has" in log_file_2
            assert '[INFO] This is info.' in log_file_2
            assert '[WARNING] This is warning.' in log_file_2
            assert '[ERROR] This is error.' in log_file_2
            assert '[CRITICAL] This is critical.' in log_file_2

            log_file_3 = pathlib.Path('log_file_1.txt').read_text()
            assert "[WARNING] File 'log_file_1.txt' has" in log_file_3
            assert '[INFO] This is info.' in log_file_3
            assert '[WARNING] This is warning.' in log_file_3
            assert '[ERROR] This is error.' in log_file_3
            assert '[CRITICAL] This is critical.' in log_file_3
