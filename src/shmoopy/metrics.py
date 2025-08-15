from typing import Callable, Optional
import functools
import pdb

db = pdb.set_trace


class MetricError(Exception):
    def __init__(self, *args, **kwargs):
        """Metric calculation error."""
        Exception.__init__(self, *args, **kwargs)


def metric(func: Optional[Callable] = None, *, validate: bool = True):
    """
    Decorator for metric functions

    Args:
        func: The function being decorated (when used without parentheses)
        validate: Whether to perform additional validation
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                raise MetricError(f'Error calculating metric "{func.__name__}": {str(e)}')
        wrapper._metric = True
        return wrapper

    # Handle both @metric and @metric() usage
    if func is not None:
        # Direct usage: @metric
        return decorator(func)
    else:
        # Called usage: @metric() or @metric(validate=False)
        return decorator
