import pytest
import shmoopy
import numpy as np
import numpy.testing as npt
from pathlib import Path


CUR_DIR = Path(__file__).parent.absolute()
DATA = 'data/tunable_load_array.txt'
DATA_BAD = 'data/tunable_load_array_bad.txt'
BAD_PATH = 'Users/dave/test.txt'


def test_tunable_load_array():
    # No type specified
    @shmoopy.tunable_load_array
    def test_values(value):
        return value

    # Working case
    values = test_values(CUR_DIR / DATA)
    npt.assert_array_equal(values, np.array([1., 2., 3., 4., 5., 6., 7.]))

    # Path is a directory
    with pytest.raises(shmoopy.TunableError) as error:
        test_values(CUR_DIR)
    assert 'Path for tunable "test_values" is not a file' in str(error.value)

    # Path does not exist
    with pytest.raises(shmoopy.TunableError) as error:
        test_values(BAD_PATH)
    assert 'Path for tunable "test_values" does not exist' in str(error.value)

    # File corrupted
    with pytest.raises(shmoopy.TunableError) as error:
        test_values(CUR_DIR / DATA_BAD)
    assert 'Could not load array from file' in str(error.value)

    # With type specified
    @shmoopy.tunable_load_array(dtype=str)
    def test_values_float(value):
        return value

    # Working case with data type specified
    values = test_values_float(CUR_DIR / DATA)
    npt.assert_array_equal(values, np.array(['1', '2', '3', '4', '5', '6', '7']))


def test_tunable_path():
    @shmoopy.tunable_path
    def test_values(value):
        return value

    # Working case with Path
    values = test_values(CUR_DIR / DATA)
    assert values == (CUR_DIR / DATA)

    # Working case with str
    values = test_values(str(CUR_DIR / DATA))
    assert values == (CUR_DIR / DATA)

    # File doesn't exist
    with pytest.raises(shmoopy.TunableError) as error:
        test_values(BAD_PATH)
    assert 'Path for tunable "test_values" does not exist' in str(error.value)

    # File is not a string or path
    with pytest.raises(shmoopy.TunableError) as error:
        test_values(123)
    assert 'Value for tunable "test_values" must be a string or pathlib.Path' in str(error.value)


def test_tunable_range():
    # Min and max defined
    @shmoopy.tunable_range(1, 10)
    def test_values(value=3):
        return value

    # Working case: use default value
    assert test_values() == 3

    # Working case: value within range
    assert test_values(5) == 5

    # Failing case: value below min
    with pytest.raises(shmoopy.TunableError) as error:
        test_values(0)
    assert 'Value for tunable "test_values" must be between 1 and 10' in str(error.value)

    # Failing case: value above max
    with pytest.raises(shmoopy.TunableError) as error:
        test_values(11)
    assert 'Value for tunable "test_values" must be between 1 and 10' in str(error.value)

    # Min only defined
    @shmoopy.tunable_range(5, None)
    def test_values(value):
        return value

    # Working case: value above min
    assert test_values(100) == 100

    # Failing case: value below min
    with pytest.raises(shmoopy.TunableError) as error:
        test_values(4)
    assert 'Value for tunable "test_values" must be greater than or equal to 5' in str(error.value)

    # Max only defined
    @shmoopy.tunable_range(None, 10)
    def test_values(value):
        return value

    # Working case: value below max
    assert test_values(5) == 5

    # Failing case: value above max
    with pytest.raises(shmoopy.TunableError) as error:
        test_values(11)
    assert 'Value for tunable "test_values" must be less than or equal to 10' in str(error.value)

    # Failing case: no value defined
    with pytest.raises(shmoopy.TunableError) as error:
        test_values()
    assert 'Tunable validation function requires a "value"' in str(error.value)

    # No min or max defined
    @shmoopy.tunable_range(None, None)
    def test_values(value):
        return value

    # Catch warning for no min or max
    with pytest.warns(UserWarning, match='Tunable range for "test_values" lacks a min or a max and is thus pointless'):
        assert test_values(5) == 5


def test_tunable_values():
    # Min and max defined
    @shmoopy.tunable_values(['hi', 5, 2.3])
    def test_values(value=5):
        return value

    # Working case: use default value
    assert test_values() == 5

    # Working case: value within allowed values
    assert test_values(2.3) == 2.3

    # Failing case: value not in allowed values
    with pytest.raises(shmoopy.TunableError) as error:
        test_values(10)
    allowed = "['hi', 5, 2.3]"
    txt = f'Value of "10" is not allowed for tunable "test_values"; allowed options are: {allowed}'
    assert txt in str(error.value)
