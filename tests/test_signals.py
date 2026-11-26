"""Signals and axes: one quantity of an analysis over all its files."""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pytest
from tests.conftest import RUNS_DIR

import psf_parser

RC = RUNS_DIR / "rc_lowpass@25.1"
SWEEPS = RUNS_DIR / "sweeps@25.1"


def _folders() -> list[Path]:
    return sorted(folder for run in RUNS_DIR.iterdir() for folder in run.iterdir() if folder.is_dir())


@pytest.fixture(params=["ascii", "binary"])
def rc(request) -> psf_parser.Database:
    return psf_parser.Database(RC / request.param)


def test_nested_sweep_is_one_array(rc):
    out = rc["mysweep/mynestedsweep/ac2"]["out"]
    assert out.values.shape == (3, 3, 61)
    assert [axis.name for axis in out.axes] == ["R1:r", "C1:c", "freq"]
    assert [axis.units for axis in out.axes] == ["Ohm", "F", "Hz"]
    assert out.axes[0].values.tolist() == [1e3, 2e3, 3e3]
    assert out.axes[1].values.tolist() == [1e-6, 2e-6, 3e-6]
    assert out.units == "V"
    assert not out.ragged


def test_nested_sweep_matches_the_rc_transfer_function(rc):
    # out / in = 1 / (1 + j 2 pi f R C), with the source at magnitude 1. An independent check that each
    # point of the array sits under the right coordinates.
    out = rc["mysweep/mynestedsweep/ac2"]["out"]
    r, c, f = (axis.values for axis in out.axes)
    expected = 1 / (1 + 2j * np.pi * f[None, None, :] * r[:, None, None] * c[None, :, None])
    assert np.allclose(out.values, expected, rtol=1e-9, atol=0.0)


def test_corner_frequency_follows_each_point(rc):
    out = rc["mysweep/mynestedsweep/ac2"]["out"]
    for i, r in enumerate(out.axes[0].values):
        for j, c in enumerate(out.axes[1].values):
            point = out[i, j]
            magnitude_db = 20 * np.log10(np.abs(point.values))
            corner = 1 / (2 * np.pi * r * c)
            below, above = point.axes[0].values < corner, point.axes[0].values > corner
            assert np.all(magnitude_db[below] > -3.0103) and np.all(magnitude_db[above] < -3.0103)


def test_ascii_and_binary_give_the_same_signals():
    ascii_db, binary_db = psf_parser.Database(RC / "ascii"), psf_parser.Database(RC / "binary")
    for path, analysis in ascii_db.analyses.items():
        for name, signal in analysis.signals.items():
            other = binary_db[path][name]
            if signal.ragged:
                assert other.ragged
                continue
            try:
                values = signal.values
            except ValueError as error:
                assert "not numbers" in str(error)  # Structs and strings come in a later step.
                continue
            assert np.array_equal(values, other.values), (path, name)
            for a, b in zip(signal.axes, other.axes, strict=True):
                assert (a.name, a.units) == (b.name, b.units)
                assert np.array_equal(a.values, b.values)


def test_indexing_drops_the_outer_axes(rc):
    out = rc["mysweep/mynestedsweep/ac2"]["out"]
    assert out[1].values.shape == (3, 61)
    assert [axis.name for axis in out[1].axes] == ["C1:c", "freq"]
    assert np.array_equal(out[1, 2].values, out.values[1, 2])
    assert np.array_equal(out[-1].values, out.values[2])
    assert out[1, 2, 0].value == out.values[1, 2, 0]


def test_indexing_rejects_slices_and_overflow(rc):
    out = rc["mysweep/mynestedsweep/ac2"]["out"]
    with pytest.raises(TypeError, match="integers"):
        out[0:2]
    with pytest.raises(IndexError, match="out of range for the R1:r axis"):
        out[3]
    with pytest.raises(IndexError, match="has 3 axes"):
        out[0, 0, 0, 0]


def test_selection_by_value(rc):
    out = rc["mysweep/mynestedsweep/ac2"]["out"]
    assert np.array_equal(out.at({"R1:r": 2000}).values, out.values[1])
    assert np.array_equal(out.at({"C1:c": 2e-6}).values, out.values[:, 1])
    assert np.array_equal(out.at({"C1:c": 3e-6, "R1:r": 1e3}).values, out.values[0, 2])
    assert out.at({"freq": 1.0}).values.shape == (3, 3)


def test_selection_lists_the_nearest_values(rc):
    out = rc["mysweep/mynestedsweep/ac2"]["out"]
    with pytest.raises(ValueError, match="R1:r = 2500: no point matches; nearest: 2000, 3000, 1000"):
        out.at({"R1:r": 2500})
    with pytest.raises(KeyError, match="no axis or parameter 'temp'"):
        out.at({"temp": 27})


def test_standalone_signal_is_its_file_variable(rc):
    out = rc["myac"]["out"]
    file = psf_parser.load(rc.folder / "myac.ac")
    assert np.array_equal(out.values, file["out"].values)
    assert [axis.name for axis in out.axes] == ["freq"]
    assert out.file.path == file.path


def test_files_follow_the_outer_axes(rc):
    out = rc["mysweep/mynestedsweep/ac2"]["out"]
    assert out.files.shape == (3, 3)
    assert out.files[1, 2] == rc.folder / "mysweep-001_mynestedsweep-002_ac2.ac"
    assert out[1, 2].file.path == out.files[1, 2]
    with pytest.raises(ValueError, match="spans 9 files"):
        _ = out.file


def test_monte_carlo_transient_is_ragged(rc):
    out = rc["mymonte/tran1"]["out"]
    assert out.ragged
    with pytest.raises(ValueError, match=r"time axis differs between the leaf files .*such as s\[0\]"):
        _ = out.values
    with pytest.raises(ValueError, match="time axis differs"):
        _ = out.axes[1].values
    assert len(out.axes[0]) == 3
    assert out.axes[0].values.tolist() == [1, 2, 3]
    lengths = sorted(len(out[i].values) for i in range(len(out.axes[0])))
    assert lengths == [62, 62, 63]


def test_paramset_axis_holds_both_parameters():
    out = psf_parser.Database(SWEEPS / "binary")["mypairs/ac1"]["out"]
    axis = out.axes[0]
    assert axis.name == "mypairs"
    assert axis.parameters["rval"].tolist() == [1e3, 2e3, 3e3]
    assert axis.parameters["cval"].tolist() == [1e-6, 2e-6, 3e-6]
    with pytest.raises(ValueError, match="sweeps rval, cval together"):
        _ = axis.values
    assert np.array_equal(out.at({"cval": 2e-6}).values, out.values[1])


def _with_parent_value(tmp_path: Path, value: str) -> psf_parser.Axis:
    """The C1:c axis of the nested sweep after its parent files' first value is rewritten."""
    folder = Path(shutil.copytree(RC / "ascii", tmp_path / "raw"))
    for index in range(3):
        parent = folder / f"mysweep-00{index}_mynestedsweep_ac2.sweep"
        text = parent.read_text()
        assert '"C1:c" 9.9999999999999995e-07' in text
        parent.write_text(text.replace('"C1:c" 9.9999999999999995e-07', f'"C1:c" {value}'))
    return psf_parser.Database(folder)["mysweep/mynestedsweep/ac2"]["out"].axes[1]


def test_parent_file_gives_full_precision_where_it_agrees(tmp_path):
    # The logFile writes six digits (format-notes 4.2), so 1.0000001e-06 agrees with its 1.00000e-06.
    axis = _with_parent_value(tmp_path, "1.0000001e-06")
    assert axis.values.tolist() == [1.0000001e-06, 2e-06, 3e-06]
    assert axis.units == "F"


def test_parent_file_that_disagrees_gives_logfile_values_without_units(tmp_path):
    axis = _with_parent_value(tmp_path, "1.1e-06")
    assert axis.values.tolist() == [1e-06, 2e-06, 3e-06]
    assert axis.units is None


def test_harmonic_level_has_logfile_values_without_units():
    # The pac parent file repeats the sidebands, so it doesn't fit the level (format-notes 4.5).
    out = psf_parser.Database(RUNS_DIR / "rf_periodic@25.1" / "ascii")["mypac"]["out"]
    assert out.axes[0].name == "harmonic"
    assert out.axes[0].units is None
    assert out.axes[0].values.tolist() == [-2, -1, 0, 1, 2]


def test_missing_leaf_is_a_hole(tmp_path):
    folder = Path(shutil.copytree(RC / "binary", tmp_path / "raw"))
    gone = folder / "mysweep-001_mynestedsweep-002_ac2.ac"
    gone.unlink()
    db = psf_parser.Database(folder)
    out = db["mysweep/mynestedsweep/ac2"]["out"]
    assert out.ragged
    with pytest.raises(ValueError, match=r"mysweep-001_mynestedsweep-002_ac2\.ac is missing"):
        _ = out.values
    assert out[0].values.shape == (3, 61)
    assert out[1, 1].values.shape == (61,)
    assert out.files[1, 2] == gone
    with pytest.raises(FileNotFoundError):
        _ = out[1, 2].file
    assert db["mysweep/ac1"]["out"].values.shape == (3, 61)


def test_values_are_read_only(rc):
    with pytest.raises(ValueError, match="read-only"):
        rc["mysweep/ac1"]["out"].values[0, 0] = 0


@pytest.mark.parametrize("folder", _folders(), ids=lambda folder: f"{folder.parent.name}/{folder.name}")
def test_every_numeric_signal_reads_or_says_it_is_ragged(folder):
    for analysis in psf_parser.Database(folder).analyses.values():
        for signal in analysis.signals.values():
            if signal.ragged:
                with pytest.raises(ValueError, match="is not one array"):
                    _ = signal.values
                continue
            try:
                values = signal.values
            except ValueError as error:
                assert "not numbers" in str(error)
                continue
            assert values.shape == tuple(len(axis) for axis in signal.axes)
