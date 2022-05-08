import io
from contextlib import redirect_stdout, redirect_stderr, contextmanager
from threading import Lock
from typing import ContextManager

from .ansi import ansi_unescape


class OutputCapture:
    def __init__(self):
        self._stdout = None
        self._stderr = None
        self._lock = Lock()
        self._lock.acquire()

    def put_result(self, stdout, stderr):
        self._stdout, self._stderr = stdout, stderr
        self._lock.release()

    @property
    def stdout(self):
        with self._lock:
            return self._stdout

    @property
    def stderr(self):
        with self._lock:
            return self._stderr


@contextmanager
def capture_output(no_ansi: bool = True) -> ContextManager[OutputCapture]:
    def _postprocess(x: str) -> str:
        if no_ansi:
            x = ansi_unescape(x)
        return x

    r = OutputCapture()
    with io.StringIO() as sout, io.StringIO() as serr:
        with redirect_stdout(sout), redirect_stderr(serr):
            yield r

        r.put_result(
            _postprocess(sout.getvalue()),
            _postprocess(serr.getvalue()),
        )
