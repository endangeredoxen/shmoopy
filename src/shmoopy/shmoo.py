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
from typing import Any, Dict, Union
import yaml
from . import utilities
from . import tunables
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
    copy_cols = []
    for column in df.columns:
        if column == 'skip_metric':
            # skip_metric is a special column name used to skip certain metric calculations
            continue

        # Parse range values
        range_rows = df[df[column].map(str).str.contains(':', na=False)]
        for irow, row in range_rows.iterrows():
            if 'log' in row[column]:
                start, stop, steps, _ = row[column].split(':')
                values = np.linspace(float(start), float(stop), int(steps))
            else:
                start, stop, steps = row[column].split(':')
                values = np.logspace(np.log10(float(start)), np.log10(float(stop)), int(steps))
            df.at[irow, column] = ' '.join([str(f) for f in values])

        # Parse load arrays of values from file using .arr extension
        array_rows = df[df[column].map(str).str.endswith('.arr')]
        if len(array_rows) > 0:
            for irow, row in array_rows.iterrows():
                df.at[irow, column] = tunables.tunable_load_array_no_decorator(row[column])

        # Make a note of copy columns to minimize looping
        if len(df[df[column].map(str).str.contains(r'^\$.*\$$', na=False)]) > 0:
            copy_cols.append(column)

        # Fix data types and explode multi-value rows
        df[column] = df[column].map(str).str.split()
        df = df.explode(column)
        df = fix_dtype(df, column)

    # Parse column copies (do it after all other parsing complete)
    for copy_col in copy_cols:
        copy_rows = df[df[copy_col].map(str).str.contains(r'^\$.*\$$', na=False)]
        for irow, row in copy_rows.iterrows():
            copy_val = copy_rows[copy_col].iloc[0].lstrip('$').rstrip('$')
            df.at[irow, copy_col] = df.loc[irow, copy_val]
        df = fix_dtype(df, copy_col)

    # Reset the index of the final csv table
    df = df.reset_index(drop=True)

    return df


def fix_dtype(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    Attept to correct DataFrame column values data types

    Args:
        df: input DataFrame
        column: name of the current column

    Returns:
        updated DataFrame
    """

    df[column] = utl.convert_numeric(df[column].replace('nan', np.nan))
    return df


def launch(
        shmoo_instance: 'ShmooClass',  # noqa: F821
        test_plan: Union[str, StringIO, Path, pd.DataFrame],
        run_func: str = 'run',
        tunable_overrides: Union[Dict[str, Any], str, Path] = None,
        optimizer=None,
        skip_validation: bool = False,
        verbose: bool = False
) -> pd.DataFrame:
    """
    Launch a shmoo based on the test_plan

    Args:
        shmoo_instance: class defining the shmoo details
        test_plan: DataFrame or path to a CSV file containing the test plan
        run_func: name of the method in shmoo_instance to call for each test case
        tunable_overrides: optional yaml file that creates or overrides tunable validation functions in the shmoo class
        skip_validation: do not validate tunable values within the csv
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
    if not skip_validation:
        if tunable_overrides is not None and isinstance(tunable_overrides, (str, Path)):
            with open(tunable_overrides, 'r') as file:
                overrides = yaml.safe_load(file)
        elif isinstance(tunable_overrides, dict):
            overrides = tunable_overrides
        else:
            overrides = {}

        test_plan = validate_tunables(test_plan, overrides, shmoo_instance)

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
            # Skip any metrics listed in the optional 'skip_metric' column
            if hasattr(row, 'skip_metric') and mm in str(row.skip_metric).split():
                continue

            # Perform the metric calculation
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


def validate_tunables(
        test_plan: pd.DataFrame,
        overrides: Dict[str, Any],
        shmoo_instance: 'ShmooClass'  # noqa: F821
) -> pd.DataFrame:
    """
    Validate all tunable parameters with @tunable_xxx decorators in the ShmooClass to ensure
    values in the test flow are allowed

    Args:
        test_plan: DataFrame containing the test flow with tunable parameters
        overrides: dict from yaml file of tunable overrides
        ShmooClass: class containing the tunable methods to validate against

    Returns:
        None, but raises TunableError if any tunable validation fails.
    """
    test_plan = test_plan.copy()
    tunable_methods = utl.find_decorated_methods(shmoo_instance, '_tunable')
    tunable_methods += [f for f in overrides.keys() if f not in tunable_methods]

    for tunable in tunable_methods:
        if tunable not in test_plan.columns:
            continue

        # Validate each tunable parameter by calling the tunable function in the shmoo class
        # and update with defaults
        for ival, value in test_plan[tunable].items():
            # Apply validation overrides first
            if tunable in overrides:
                test_plan.at[ival, tunable] = tunables.validate_from_override(tunable, value, overrides[tunable])

            else:
                # Use decorated shmoo class methods next
                if isinstance(value, float) and np.isnan(value):
                    # Ignore NaN values in order to preserve defaults
                    test_plan.at[ival, tunable] = getattr(shmoo_instance, tunable)()
                else:
                    test_plan.at[ival, tunable] = getattr(shmoo_instance, tunable)(value)

    return test_plan
