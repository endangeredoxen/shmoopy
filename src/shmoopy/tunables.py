from typing import Any, List, Union
from pathlib import Path
import numpy as np
import shmoopy
import warnings
import inspect
import functools
import pdb
import os

db = pdb.set_trace


class TunableError(Exception):
    def __init__(self, *args, **kwargs):
        """Tunable validation error."""
        Exception.__init__(self, *args, **kwargs)


class TunableWarning(Warning):
    pass


warnings.simplefilter('once', TunableWarning)


def _handle_defaults(args, kwargs, func):
    # Check for "self"
    is_default = False
    if len(args) == 2 and hasattr(args[0], '__class__'):
        value = args[1]
    elif len(args) == 1 and not hasattr(args[0], '__class__'):
        value = args[0]
    else:
        # Get the default value from the decorated function's signature
        sig = inspect.signature(func)
        if 'value' in sig.parameters and sig.parameters['value'].default is not inspect.Parameter.empty:
            value = sig.parameters['value'].default
        else:
            raise TunableError('Tunable validation function requires a "value"')
        is_default = True
    return value, is_default


def _validate_path(value, func_name):
    """Helper function to validate and return a Path object"""
    if isinstance(value, str):
        fpath = Path(value)  # Fixed: was fpath(value)
    elif isinstance(value, Path):
        fpath = value
    else:
        raise TunableError(f'Value for tunable "{func_name}" must be a string or pathlib.Path')

    file_exists = False
    # Check if the path as listed exists
    if fpath.exists():
        file_exists = True
    # Check the relative path to the current working directory
    elif (Path(os.getcwd()) / fpath).exists():
        file_exists = True
        fpath = Path(os.getcwd()) / fpath
    # Check the examples directory
    elif (Path(shmoopy.__file__).parent / fpath).exists():
        file_exists = True
        fpath = Path(shmoopy.__file__).parent / fpath
    if not file_exists:
        raise TunableError(f'Path for tunable "{func_name}" does not exist: {fpath}')

    return str(fpath)


def tunable_load_array(func=None, *, dtype=None):
    """
    Read a list of values for a tunable from file after checking the fpath is valid

    Returns:
        values from file as numpy array
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            value, is_default = _handle_defaults(args, kwargs, func)
            if is_default:
                # ignore path check and just use default
                return value
            fname = func.__name__
            fpath = _validate_path(value, fname)
            if not fpath.is_file():
                raise TunableError(f'Path for tunable "{fname}" is not a file: {fpath}')
            try:
                values = np.loadtxt(fpath, dtype=dtype)
            except ValueError:
                raise TunableError(f'Could not load array from file "{fpath}" for tunable "{fname}"')
            return values
        wrapper._tunable = True
        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


def tunable_path(func):
    """
    Ensure a tunable value that represents a fpath exists

    Returns:
        a validated fpath to use in a shmoo test case
    """
    def wrapper(*args, **kwargs):
        value, is_default = _handle_defaults(args, kwargs, func)
        if isinstance(value, float) and np.isnan(value):
            # ignore nan
            return value
        fname = func.__name__
        return _validate_path(value, fname)
    wrapper._tunable = True
    return wrapper


def tunable_range(min_value: Union[int, float, None], max_value: Union[int, float, None]):
    """
    Ensure a tunable value falls within a certain range

    Args:
        min_value: minimum allowed value; use None for no minimum limit
        max_value: maximum allowed value; use None for no maximum limit

    Returns:
        a validated value to use in a shmoo test case
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            value, is_default = _handle_defaults(args, kwargs, func)
            if isinstance(value, float) and np.isnan(value):
                # ignore nan
                return value
            fname = func.__name__
            if min_value is None and max_value is None:
                warnings.warn(f'Tunable range for "{fname}" lacks a min or a max and is thus pointless')
            elif min_value is None and value > max_value:
                raise TunableError(f'Value for tunable "{fname}" must be less than or equal to {max_value}')
            elif max_value is None and value < min_value:
                raise TunableError(f'Value for tunable "{fname}" must be greater than or equal to {min_value}')
            elif min_value is not None and max_value is not None and not min_value <= value <= max_value:
                raise TunableError(f'Value for tunable "{fname}" must be between {min_value} and {max_value}')
            return func(*args, **kwargs)
        wrapper._tunable = True
        return wrapper
    return decorator


def tunable_values(values: List[Any]):
    """
    Ensure a tunable value is contained in a list of allowed values

    Args:
        values: list of allowed choices for the tunable parameter

    Returns:
        a validated value to use in a shmoo test case
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            value, is_default = _handle_defaults(args, kwargs, func)
            fname = func.__name__
            if value not in values:
                valid = [f"'{item}'" if isinstance(item, str) else str(item) for item in values]
                raise TunableError(f'Value of "{value}" is not allowed for tunable "{fname}"; allowed options '
                                   f'are: [{", ".join(valid)}]')
            return func(*args, **kwargs)
        wrapper._tunable = True
        return wrapper
    return decorator
