from pathlib import Path
import pandas as pd
import numpy as np
import inspect
import pdb

db = pdb.set_trace


# Read the package version file
with open(Path(__file__).parent / 'version.txt', 'r') as fid:
    __version__ = fid.readlines()[0].replace('\n', '')


def can_convert_to_int(series):
    try:
        cleaned = series.replace('nan', np.nan)
        numeric = pd.to_numeric(cleaned, errors='raise')
        return numeric.dropna().apply(lambda x: x == int(x)).all()
    except ValueError:
        return False


def can_convert_to_float(series):
    try:
        pd.to_numeric(series.replace('nan', np.nan), errors='raise')
        return True
    except ValueError:
        return False


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
