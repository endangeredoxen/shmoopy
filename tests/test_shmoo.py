import pytest
import shmoopy
import numpy as np
import numpy.testing as npt
from shmoopy.metrics import metric
from shmoopy.examples.tonemap import ToneMapShmoo
import os
from types import MethodType
import pdb
from pathlib import Path
osjoin = os.path.join
db = pdb.set_trace


TONEMAP_PATH = Path(shmoopy.examples.tonemap.__file__).parent


def test_shmoo_simple(tonemap_shmoo, csv_gamma_only):
    results = shmoopy.launch(tonemap_shmoo, csv_gamma_only, verbose=True)

    expected = np.array([5.10870616e-01, 1.03579909e+01, 2.84290365e+01, 1.47935432e+02,
                         1.90343056e+02, 2.08684807e+02, 1.75730387e-03, 1.99563726e+00, 1.13781605e+01])
    npt.assert_array_almost_equal(results['mean'], expected)


def test_shmoo_simple_bad_metric(csv_gamma_only):
    @metric
    def bad_metric(self, values):
        print(values['dope'])

    tonemap2 = ToneMapShmoo()
    tonemap2.bad_metric = MethodType(bad_metric, tonemap2)
    with pytest.raises(shmoopy.shmoo.ShmooMetricError) as error:
        shmoopy.launch(tonemap2, csv_gamma_only)
    assert 'Error calculating metric "bad_metric" for row 0: ' in str(error.value)
    assert 'dope' in str(error.value)


def test_shmoo_simple_skip_metric(tonemap_shmoo, csv_gamma_only):
    tp = shmoopy.create_test_plan(csv_gamma_only)
    tp['skip_metric'] = 'stats'
    results = shmoopy.launch(tonemap_shmoo, tp)
    assert 'mean' not in results.columns


def test_shmoo_simple_bad_run(tonemap_shmoo, csv_gamma_only):
    with pytest.raises(shmoopy.shmoo.ShmooRunError) as error:
        shmoopy.launch(tonemap_shmoo, csv_gamma_only, run_func='yo_bro')
    assert 'ShmooClass ToneMapShmoo does not have a method named "yo_bro"' in str(error.value)


def test_shmoo_simple_bad_csv(tonemap_shmoo):
    with pytest.raises(TypeError) as error:
        shmoopy.launch(tonemap_shmoo, 4)
    assert 'test_plan must be a pd.DataFrame, str, pathlib.Path, or StringIO object' in str(error.value)

    with pytest.raises(FileNotFoundError) as error:
        shmoopy.launch(tonemap_shmoo, 'hi.csv')
    assert 'CSV file does not exist: hi.csv' in str(error.value)


def test_shmoo_override_causes_range_error(tonemap_shmoo, csv_gamma_only):
    with pytest.raises(shmoopy.TunableError) as error:
        shmoopy.launch(tonemap_shmoo, csv_gamma_only, tunable_overrides=TONEMAP_PATH / 'tunable_yaml.yaml')
    assert 'Value for tunable "gamma" must be greater than or equal to 2 (per override)' in str(error.value)


def test_shmoo_override_by_dict(tonemap_shmoo, csv_gamma_only):
    with pytest.raises(shmoopy.TunableError) as error:
        shmoopy.launch(tonemap_shmoo, csv_gamma_only, tunable_overrides={'algorithm': {'values': ['hi']}})
    assert '"drago" is not allowed for tunable "algorithm"; allowed options are: [\'hi\'] (per override)' \
        in str(error.value)
