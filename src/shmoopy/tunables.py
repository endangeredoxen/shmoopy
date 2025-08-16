from typing import Any, Callable, Dict, List, Tuple, Union
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


def _handle_defaults(args: Tuple[Any, ...], kwargs: dict, func: Callable) -> Tuple[Any, bool]:
    """
    Handles tunable function arguments to retrieve the value and determine if it's a default.

    This function is designed to work with both standalone functions and class methods.
    It checks the function's signature to correctly extract the 'value' argument.
    """
    sig = inspect.signature(func)
    params = list(sig.parameters.keys())

    # Determine if the function is a method by checking for 'self' as the first parameter
    is_method = params and params[0] == 'self'

    # The index of the 'value' parameter in the positional arguments list
    value_index = 1 if is_method else 0

    # Case 1: 'value' is provided as a positional argument
    if len(args) > value_index:
        value = args[value_index]
        is_default = False
    # Case 2: 'value' is provided as a keyword argument
    elif 'value' in kwargs:
        value = kwargs['value']
        is_default = False
    # Case 3: Use the default value from the function signature
    else:
        if 'value' in sig.parameters and sig.parameters['value'].default is not inspect.Parameter.empty:
            value = sig.parameters['value'].default
            is_default = True
        else:
            # This handles cases where 'value' isn't provided and has no default
            raise TunableError('Tunable validation function requires a "value" argument or a default value')

    return value, is_default


def _validate_path(value, func_name):
    """Helper function to validate and return a Path object"""
    if isinstance(value, str):
        fpath = Path(value)
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
            fpath = Path(_validate_path(value, fname))
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


def tunable_load_array_no_decorator(value, dtype=None):
    """
    Read a list of values for a tunable from file after checking the fpath is valid

    Returns:
        values from file as numpy array
    """
    fname = ''
    fpath = Path(_validate_path(value, fname))
    if not fpath.is_file():
        raise TunableError(f'Path for tunable "{fname}" is not a file: {fpath}')
    try:
        values = np.loadtxt(fpath, dtype=dtype)
    except ValueError:
        raise TunableError(f'Could not load array from file "{fpath}" for tunable "{fname}"')
    return ' '.join([str(f) for f in values])


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
                warnings.warn(f'Tunable range for "{fname}" lacks a min or a max and is thus pointless', TunableWarning)
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


def validate_from_override(tunable: str, value: Any, override: Dict[str, Any]) -> Any:
    """
    Validate a tunable parameter based on and override dictionay

    Args:
        tunable: name of the tunable
        value: value to check
        override: dictionary of limits to check

    Returns:
        validated value
    """
    # Case @tunable_range
    if 'min' in override or 'max' in override:
        if 'min' in override and value < override['min']:
            raise TunableError(f'Value for tunable "{tunable}" must be greater than or equal to {override["min"]} '
                               '(per override)')
        if 'max' in override and value > override['max']:
            raise TunableError(f'Value for tunable "{tunable}" must be less than or equal to {override["max"]} '
                               '(per override)')

    # Case @tunable_values
    elif 'values' in override:
        if value not in override['values']:
            valid = [f"'{item}'" if isinstance(item, str) else str(item) for item in override["values"]]
            raise TunableError(f'Value of "{value}" is not allowed for tunable "{tunable}"; allowed options '
                               f'are: [{", ".join(valid)}] (per override)')

    else:
        raise TunableError(f'Override for "{tunable}" is malformatted; please try again')

    return value
