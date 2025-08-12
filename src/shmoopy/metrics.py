from typing import Any, Dict, List, Union
from pathlib import Path
import numpy as np
import warnings
import inspect
import functools
import pdb

db = pdb.set_trace
warnings.simplefilter('always', UserWarning)


class MetricError(Exception):
    def __init__(self, *args, **kwargs):
        """Metric calculation error."""
        Exception.__init__(self, *args, **kwargs)


def metric(values: Dict[Any]):
    """
    Ensure a tunable value is contained in a list of allowed values

    Args:
        values: list of allowed choices for the tunable parameter

    Returns:
        a validated value to use in a shmoo test case
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                raise MetricError(f'Error calculating metric "{func.__name__}": {str(e)}')
        wrapper._metric = True
        return wrapper
    return decorator