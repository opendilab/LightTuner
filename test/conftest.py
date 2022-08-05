import os
from functools import lru_cache
from typing import Iterator, Optional
from unittest.mock import patch, MagicMock

import pytest
from ditk import logging


@lru_cache()
def _mock_cpu_count() -> Optional[int]:
    if os.environ.get('CPU_COUNT'):
        return int(os.environ['CPU_COUNT'])
    else:
        return None


@pytest.fixture(scope="session", autouse=True)
def cpu_count_mocker() -> Iterator[None]:
    _cpu_count = _mock_cpu_count()
    if _cpu_count is not None:
        logging.info(f"CPU_COUNT env detected, return value of os.cpu_count() will be mocked as {_cpu_count}.")
        with patch("os.cpu_count", MagicMock(return_value=_cpu_count)):
            yield
        logging.info("Mock of os.cpu_count() has been quited.")

    else:
        yield
