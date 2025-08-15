############################################################################
# shmoo.py
#   Main setup functions to enable a multivariate sweep or shmoo and
#   validate across multiple metrics.
############################################################################

__author__ = 'Steve Nicholes'
__copyright__ = 'Copyright (C) 2025 Steve Nicholes'
__license__ = 'MIT'
__url__ = 'https://github.com/endangeredoxen/shmoopy'

import pandas as pd
import numpy as np
import uuid
from pathlib import Path
from io import StringIO
from typing import Union
from . import utilities
import pdb

db = pdb.set_trace
utl = utilities
__version__ = utilities.__version__


class ShmooMetricError(Exception):
    def __init__(self, *args, **kwargs):
        """Shmoo metric calculation error."""
        Exception.__init__(self, *args, **kwargs)


class ShmooRunError(Exception):
    def __init__(self, *args, **kwargs):
        """Shmoo run error."""
        Exception.__init__(self, *args, **kwargs)


def create_test_plan(csv_file: Union[str, StringIO, Path]) -> pd.DataFrame:
    """
    Create a test plan from a CSV file or StringIO object.  Handles explosion of tunable
    parameters to create multiple test plan rows for a single csv entry.

    Args:
        csv_file: path to the CSV file or a StringIO object containing the CSV data.

    Returns:
        DataFrame containing the exploded test plan.
    """
    # Read the csv file into a DataFrame
    if isinstance(csv_file, (str, Path)):
        csv_file = Path(csv_file)
        if not csv_file.exists():
            raise FileNotFoundError(f'CSV file does not exist: {csv_file}')
    elif not isinstance(csv_file, StringIO):
        raise TypeError('csv_file must be a str, pathlib.Path, or StringIO object')

    df = pd.read_csv(csv_file)

    # Parse tunable parameters and explode the DataFrame
    for column in df.columns:
        # Parse 1: range values
        range_rows = df[df[column].map(str).str.contains(':', na=False)]
        if len(range_rows) > 0:
            for irow, row in range_rows.iterrows():
                is_log = False
                if 'log' in row:
                    is_log = True
                start, stop, steps = row[column].split(':')
                if is_log:
                    values = np.logspace(float(start), float(stop), int(steps))
                else:
                    values = np.linspace(float(start), float(stop), int(steps))
                df.at[irow, column] = ' '.join([str(f) for f in values])

        # Parse 2: copy values with $xxx$

        # Parse 3: load arrays of values from file using .arr extension
        array_rows = df[df[column].map(str).str.endswith('.arr')]
        if len(array_rows) > 0:
            for irow, row in array_rows.iterrows():
                db()
                if not Path(row[column]).exists():
                    raise FileNotFoundError(f'Array file does not exist: {row[column]}')
                try:
                    values = np.loadtxt(row[column])
                except Exception as e:
                    raise ValueError(f'Could not load array from file {row[column]}: {str(e)}')
                df.at[irow, column] = ' '.join([str(f) for f in values])

        # Fix data types and explode multi-value rows
        df = explode_column(df, column)

    df = df.reset_index(drop=True)

    return df


def explode_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
    # Split string values into lists and explode!
    df[column] = df[column].map(str).str.split()
    df = df.explode(column)

    # Fix data types
    df[column] = df[column].replace('nan', np.nan)
    if utl.can_convert_to_int(df[column]):
        df[column] = df[column].astype('float64').astype('Int64')
    elif utl.can_convert_to_float(df[column]):
        df[column] = df[column].astype('float64')

    return df


def launch(
        shmoo_instance: 'ShmooClass',  # noqa: F821
        test_plan: Union[str, StringIO, Path, pd.DataFrame],
        run_func='run',
        optimizer=None,
        verbose=False
) -> pd.DataFrame:
    """
    Launch a shmoo based on the test_plan

    Args:
        shmoo_instance: class defining the shmoo details
        test_plan: DataFrame or path to a CSV file containing the test plan
        run_func: name of the method in shmoo_instance to call for each test case
        optimizer: TODO

    Returns:
        DataFrame containing the results of the shmoo test cases
    """
    # Get the test plan
    if isinstance(test_plan, (str, Path, StringIO)):
        test_plan = create_test_plan(Path(test_plan))
    elif not isinstance(test_plan, pd.DataFrame):
        raise TypeError('test_plan must be a pd.DataFrame, str, pathlib.Path, or StringIO object')

    # Validate tunables within the test plan
    test_plan = validate_tunables(test_plan, shmoo_instance)

    # Add a unique identifier for the test to each row for tracking
    test_plan['uuid'] = uuid.uuid1()

    # Get the metric methods from the ShmooClass
    metric_methods = utl.find_decorated_methods(shmoo_instance, '_metric')

    # Make sure the run function exists in the class
    if not hasattr(shmoo_instance, run_func):
        shmoo_name = shmoo_instance.__class__.__name__
        raise ShmooRunError(f'ShmooClass {shmoo_name} does not have a method named "{run_func}"')

    # Launch the test
    results = []
    for row in test_plan.itertuples():
        if verbose:
            print(f'Running test case {row.Index + 1}/{len(test_plan)}...', end='')
        # Call the run function
        row_results = row._asdict()
        row_locals = getattr(shmoo_instance, run_func)(row.Index, row)

        # Run metric calculations
        for mm in metric_methods:
            try:
                row_results.update(getattr(shmoo_instance, mm)(row_locals))
            except Exception as e:
                raise ShmooMetricError(f'Error calculating metric "{mm}" for row {row.Index}: {str(e)}')

        results.append(row_results)

        if verbose:
            print(' done')

    # Return the results as a DataFrame
    results = pd.DataFrame(results)
    return results


def validate_tunables(test_plan: pd.DataFrame, shmoo_instance: 'ShmooClass') -> pd.DataFrame:  # noqa: F821
    """
    Validate all tunable parameters with @tunable_xxx decorators in the ShmooClass to ensure
    values in the test flow are allowed

    Args:
        test_plan: DataFrame containing the test flow with tunable parameters
        ShmooClass: class containing the tunable methods to validate against

    Returns:
        None, but raises TunableError if any tunable validation fails.
    """
    test_plan = test_plan.copy()
    tunable_methods = utl.find_decorated_methods(shmoo_instance, '_tunable')

    for tunable in tunable_methods:
        if tunable not in test_plan.columns:
            continue

        # Validate each tunable parameter by calling the tunable function in the shmoo class
        # and update with defaults
        for ival, value in test_plan[tunable].items():
            if isinstance(value, float) and np.isnan(value):
                # Ignore NaN values in order to preserve defaults
                test_plan.at[ival, tunable] = getattr(shmoo_instance, tunable)()
            else:
                test_plan.at[ival, tunable] = getattr(shmoo_instance, tunable)(value)

    return test_plan
