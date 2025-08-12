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
from pathlib import Path
from io import StringIO
from typing import Union
from . import utilities
import pdb

db = pdb.set_trace
utl = utilities
__version__ = utilities.__version__


def create_test_plan(csv_file: Union[str, StringIO, Path]) -> pd.DataFrame:
    """
    Create a test plan from a CSV file or StringIO object.  Handles explosion of tunable
    parameters to create multiple test plan rows for a single csv entry.

    Args:
        csv_file: Path to the CSV file or a StringIO object containing the CSV data.

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
        df[column] = df[column].str.split()
        df = df.explode(column)

    df = df.reset_index(drop=True)

    return df


def validate_tunables():
    # Validate tunable parameters
    tunable_methods = utl.find_decorated_methods(ShmooClass, '_tunable')




def shmoo(ShmooClass):

    # Validate tunable parameters
    tunable_methods = utl.find_decorated_methods(ShmooClass, '_tunable')

    db()
