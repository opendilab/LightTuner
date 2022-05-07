import pytest
from testfixtures import TempDirectory


@pytest.fixture()
def dir_():
    with TempDirectory() as directory:
        yield directory
