import os
import tempfile
from contextlib import contextmanager


@contextmanager
def tempdir():
    _original_path = os.path.abspath(os.curdir)
    with tempfile.TemporaryDirectory() as dirname:
        try:
            os.chdir(dirname)
            yield
        finally:
            os.chdir(_original_path)
