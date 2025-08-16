import pytest
import shmoopy
from shmoopy.examples.tonemap import ToneMapShmoo
from pathlib import Path


TONEMAP_PATH = Path(shmoopy.examples.tonemap.__file__).parent


@pytest.fixture(scope="session")
def tonemap_shmoo():
    shmoo = ToneMapShmoo()
    yield shmoo  # Yield the instance to the tests


@pytest.fixture(scope="session")
def csv_gamma_only():
    yield TONEMAP_PATH / 'gamma_only.csv'


@pytest.fixture(scope="session")
def csv_multiple():
    yield TONEMAP_PATH / 'multiple.csv'
