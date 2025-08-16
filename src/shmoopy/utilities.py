from pathlib import Path
import pandas as pd
import inspect
import pdb
db = pdb.set_trace


# Read the package version file
with open(Path(__file__).parent / 'version.txt', 'r') as fid:
    __version__ = fid.readlines()[0].replace('\n', '')


def convert_numeric(series: pd.Series) -> pd.Series:
    """
    Converts a pandas Series to the most appropriate numeric type (Int64, float64).
    Leaves string or other non-numeric types as they are.

    Args:
        series: The pandas Series to convert.

    Returns:
        The converted pandas Series.
    """
    try:
        # Use pandas to_numeric with 'coerce' to handle non-numeric values
        # This will turn values that cannot be converted into NaN
        numeric_series = pd.to_numeric(series, errors='raise')

        # Check if the series can be represented as an integer
        # We need to drop NA values first before checking.
        if (numeric_series.dropna() % 1 == 0).all():
            return numeric_series.astype('Int64')  # Use nullable integer type
        else:
            return numeric_series.astype('float64')

    except Exception:
        # Return the original series if conversion fails for any reason
        return series


def find_decorated_methods(cls, attribute_name: str) -> list:
    """
    Find all decorated methods with a specific defined attribute.  Used to find
    tunable and metric methods in a ShmooClass.

    Args:
        cls: class or class instance to search for decorated methods
        attribute_name: name of the attribute to look for in the method

    Returns:
        list of method names that have the specified attribute
    """
    try:
        return [name for name, method in inspect.getmembers(cls, inspect.ismethod)
                if hasattr(method, attribute_name)]
    except TypeError:
        return [name for name, method in inspect.getmembers(cls.__class__, inspect.isfunction)
                if hasattr(method, attribute_name)]
