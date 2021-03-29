import json
import os

import pytest
import xarray as xr

from qcodes import new_data_set
from qcodes.dataset.descriptions.dependencies import InterDependencies_
from qcodes.dataset.descriptions.param_spec import ParamSpecBase
from qcodes.dataset.export_config import DataExportType
from qcodes.dataset.descriptions.versioning import serialization as serial


@pytest.mark.usefixtures('experiment')
@pytest.fixture(name="mock_dataset")
def _make_mock_dataset():
    dataset = new_data_set("dataset")
    xparam = ParamSpecBase("x", 'numeric')
    yparam = ParamSpecBase("y", 'numeric')
    zparam = ParamSpecBase("z", 'numeric')
    idps = InterDependencies_(
        dependencies={yparam: (xparam,), zparam: (xparam,)})
    dataset.set_interdependencies(idps)

    dataset.mark_started()
    results = [{'x': 0, 'y': 1, 'z': 2}]
    dataset.add_results(results)
    dataset.mark_completed()
    return dataset


@pytest.mark.usefixtures('experiment')
@pytest.fixture(name="mock_dataset_nonunique")
def _make_mock_dataset_nonunique_index():
    dataset = new_data_set("dataset")
    xparam = ParamSpecBase("x", 'numeric')
    yparam = ParamSpecBase("y", 'numeric')
    zparam = ParamSpecBase("z", 'numeric')
    idps = InterDependencies_(
        dependencies={yparam: (xparam,), zparam: (xparam,)})
    dataset.set_interdependencies(idps)

    dataset.mark_started()
    results = [{'x': 0, 'y': 1, 'z': 2}, {'x': 0, 'y': 1, 'z': 2}]
    dataset.add_results(results)
    dataset.mark_completed()
    return dataset


@pytest.mark.usefixtures('experiment')
def test_write_data_to_text_file_save(tmp_path_factory):
    dataset = new_data_set("dataset")
    xparam = ParamSpecBase("x", 'numeric')
    yparam = ParamSpecBase("y", 'numeric')
    idps = InterDependencies_(dependencies={yparam: (xparam,)})
    dataset.set_interdependencies(idps)

    dataset.mark_started()
    results = [{'x': 0, 'y': 1}]
    dataset.add_results(results)
    dataset.mark_completed()

    path = str(tmp_path_factory.mktemp("write_data_to_text_file_save"))
    dataset.write_data_to_text_file(path=path)
    assert os.listdir(path) == ['y.dat']
    with open(os.path.join(path, "y.dat")) as f:
        assert f.readlines() == ['0.0\t1.0\n']


@pytest.mark.usefixtures('experiment')
def test_write_data_to_text_file_save_multi_keys(tmp_path_factory, mock_dataset):
    tmp_path = tmp_path_factory.mktemp("data_to_text_file_save_multi_keys")
    path = str(tmp_path)
    mock_dataset.write_data_to_text_file(path=path)
    assert sorted(os.listdir(path)) == ['y.dat', 'z.dat']
    with open(os.path.join(path, "y.dat")) as f:
        assert f.readlines() == ['0.0\t1.0\n']
    with open(os.path.join(path, "z.dat")) as f:
        assert f.readlines() == ['0.0\t2.0\n']


@pytest.mark.usefixtures('experiment')
def test_write_data_to_text_file_save_single_file(tmp_path_factory, mock_dataset):
    tmp_path = tmp_path_factory.mktemp("to_text_file_save_single_file")
    path = str(tmp_path)
    mock_dataset.write_data_to_text_file(path=path, single_file=True,
                                         single_file_name='yz')
    assert os.listdir(path) == ['yz.dat']
    with open(os.path.join(path, "yz.dat")) as f:
        assert f.readlines() == ['0.0\t1.0\t2.0\n']


@pytest.mark.usefixtures('experiment')
def test_write_data_to_text_file_length_exception(tmp_path):
    dataset = new_data_set("dataset")
    xparam = ParamSpecBase("x", 'numeric')
    yparam = ParamSpecBase("y", 'numeric')
    zparam = ParamSpecBase("z", 'numeric')
    idps = InterDependencies_(
        dependencies={yparam: (xparam,), zparam: (xparam,)})
    dataset.set_interdependencies(idps)

    dataset.mark_started()
    results1 = [{'x': 0, 'y': 1}]
    results2 = [{'x': 0, 'z': 2}]
    results3 = [{'x': 1, 'z': 3}]
    dataset.add_results(results1)
    dataset.add_results(results2)
    dataset.add_results(results3)
    dataset.mark_completed()

    temp_dir = str(tmp_path)
    with pytest.raises(Exception, match='different length'):
        dataset.write_data_to_text_file(path=temp_dir, single_file=True,
                                        single_file_name='yz')


@pytest.mark.usefixtures('experiment')
def test_write_data_to_text_file_name_exception(tmp_path, mock_dataset):
    temp_dir = str(tmp_path)
    with pytest.raises(Exception, match='desired file name'):
        mock_dataset.write_data_to_text_file(path=temp_dir, single_file=True,
                                             single_file_name=None)


@pytest.mark.usefixtures('experiment')
def test_export_csv(tmp_path_factory, mock_dataset):
    tmp_path = tmp_path_factory.mktemp("export_csv")
    path = str(tmp_path)
    mock_dataset.export(export_type="csv", path=path, prefix="qcodes_")
    assert os.listdir(path) == [f"qcodes_{mock_dataset.run_id}.csv"]
    with open(os.path.join(path, f"qcodes_{mock_dataset.run_id}.csv")) as f:
        assert f.readlines() == ['0.0\t1.0\t2.0\n']


@pytest.mark.usefixtures('experiment')
def test_export_netcdf(tmp_path_factory, mock_dataset):
    tmp_path = tmp_path_factory.mktemp("export_netcdf")
    path = str(tmp_path)
    mock_dataset.export(export_type="netcdf", path=path, prefix="qcodes_")
    assert os.listdir(path) == [f"qcodes_{mock_dataset.run_id}.nc"]
    file_path = os.path.join(path, f"qcodes_{mock_dataset.run_id}.nc")
    ds = xr.open_dataset(file_path)
    df = ds.to_dataframe()
    assert df.index.name == "x"
    assert df.index.values.tolist() == [0.]
    assert df.y.values.tolist() == [1.0]
    assert df.z.values.tolist() == [2.0]


@pytest.mark.usefixtures('experiment')
def test_export_no_or_nonexistent_type_specified(tmp_path_factory, mock_dataset):
    with pytest.raises(ValueError):
        mock_dataset.export()

    with pytest.raises(ValueError):
        mock_dataset.export(export_type="foo")


@pytest.mark.usefixtures('experiment')
def test_export_from_config(tmp_path_factory, mock_dataset, mocker):
    tmp_path = tmp_path_factory.mktemp("export_from_config")
    path = str(tmp_path)
    mock_type = mocker.patch("qcodes.dataset.data_set.get_data_export_type")
    mock_path = mocker.patch("qcodes.dataset.data_set.get_data_export_path")
    mock_type.return_value = DataExportType.CSV
    mock_path.return_value = path
    mock_dataset.export()
    assert os.listdir(path) == [f"qcodes_{mock_dataset.run_id}.csv"]


def test_same_setpoint_warning_for_df_and_xarray(different_setpoint_dataset):

    warning_message = (
        "Independent parameter setpoints are not equal. "
        "Check concatenated output carefully."
    )

    with pytest.warns(UserWarning, match=warning_message):
        different_setpoint_dataset.to_pandas_dataframe()

    with pytest.warns(UserWarning, match=warning_message):
        different_setpoint_dataset.to_xarray_dataset()

    with pytest.warns(UserWarning, match=warning_message):
        different_setpoint_dataset.cache.to_pandas_dataframe()

    with pytest.warns(UserWarning, match=warning_message):
        different_setpoint_dataset.cache.to_xarray_dataset()


def test_export_to_xarray(mock_dataset):
    ds = mock_dataset.to_xarray_dataset()
    assert len(ds) == 2
    assert "index" not in ds.coords
    assert "x" in ds.coords
    _assert_xarray_metadata_is_as_expected(ds, mock_dataset)


def test_export_to_xarray_non_unique_dependent_parameter(mock_dataset_nonunique):
    """When x (the dependent parameter) contains non unique values it cannot be used
    as coordinates in xarray so check that we fall back to using an index"""
    ds = mock_dataset_nonunique.to_xarray_dataset()
    assert len(ds) == 3
    assert "index" in ds.coords
    assert "x" not in ds.coords
    _assert_xarray_metadata_is_as_expected(ds, mock_dataset_nonunique)

    for array_name in ds.data_vars:
        assert "snapshot" not in ds[array_name].attrs.keys()


def test_export_to_xarray_extra_metadata(mock_dataset):
    mock_dataset.add_metadata("mytag", "somestring")
    mock_dataset.add_metadata("myothertag", 1)
    ds = mock_dataset.to_xarray_dataset()

    _assert_xarray_metadata_is_as_expected(ds, mock_dataset)

    for array_name in ds.data_vars:
        assert "snapshot" not in ds[array_name].attrs.keys()


def test_export_to_xarray_ds_dict_extra_metadata(mock_dataset):
    mock_dataset.add_metadata("mytag", "somestring")
    mock_dataset.add_metadata("myothertag", 1)
    da_dict = mock_dataset.to_xarray_dataarray_dict()

    for datarray in da_dict.values():
        _assert_xarray_metadata_is_as_expected(datarray, mock_dataset)


def _assert_xarray_metadata_is_as_expected(xarray_ds, qc_dataset):

    assert xarray_ds.ds_name == qc_dataset.name
    assert xarray_ds.sample_name == qc_dataset.sample_name
    assert xarray_ds.exp_name == qc_dataset.exp_name
    assert xarray_ds.snapshot == json.dumps(qc_dataset.snapshot)
    assert xarray_ds.guid == qc_dataset.guid
    assert xarray_ds.run_timestamp == qc_dataset.run_timestamp()
    assert xarray_ds.completed_timestamp == qc_dataset.completed_timestamp()
    assert xarray_ds.captured_run_id == qc_dataset.captured_run_id
    assert xarray_ds.captured_counter == qc_dataset.captured_counter
    assert xarray_ds.run_id == qc_dataset.run_id
    assert xarray_ds.run_description == serial.to_json_for_storage(qc_dataset.description)
