import pytest
import shmoopy
from shmoo_tonemap import ToneMapShmoo
from pathlib import Path


@pytest.fixture(scope="session")
def test_shmoo():
    shmoo = ToneMapShmoo()
    yield shmoo  # Yield the instance to the tests
    shmoo.cleanup() # Teardown logic after tests