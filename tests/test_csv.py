# This file tests everything related to csv parsing and validation

import pytest
import shmoopy
from io import StringIO
import pandas as pd
import numpy as np
import numpy.testing as npt
import os
import pdb
osjoin = os.path.join
db = pdb.set_trace


def test_create_test_plan_string(csv_gamma_only):
    csv = shmoopy.create_test_plan(str(csv_gamma_only))

    assert len(csv) == 9


def test_create_test_plan_path(csv_gamma_only):
    csv = shmoopy.create_test_plan(csv_gamma_only)

    assert len(csv) == 9


def test_create_test_plan_stringio(csv_gamma_only):
    csv = StringIO('algorithm,gamma,image_src\ndrago reinhard mantiuk,1 2 3,'
                   'examples/tonemap/cobblestone_street_night_1k.hdr')
    csv = shmoopy.create_test_plan(csv)

    assert len(csv) == 9


def test_create_test_plan_bad_path():
    with pytest.raises(FileNotFoundError):
        shmoopy.create_test_plan('hi.csv')


def test_create_test_plan_bad_path2():
    with pytest.raises(TypeError):
        shmoopy.create_test_plan(2)


def test_create_test_plan_magic_syntax(csv_multiple):
    csv = shmoopy.create_test_plan(csv_multiple)

    assert len(csv) == 21
    npt.assert_array_equal(pd.unique(csv.loc[csv.algorithm == 'mantiuk', 'scale']),
                           np.array([0.2, 0.7, 1.1]))
