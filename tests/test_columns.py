"""What `Variable.values` and `Variable.value` hold, and how psfbin value sections get decoded."""

from __future__ import annotations

import struct
from pathlib import Path

import numpy as np
import pytest

import psf_parser
from psf_parser.errors import PsfParseError

RUN = Path(__file__).parent / "data" / "runs" / "rc_lowpass@1.4.0"
ENCODINGS = ["ascii", "binary"]


@pytest.mark.parametrize("encoding", ENCODINGS)
def test_sweep_is_a_float_array(encoding):
    freq = psf_parser.load(RUN / encoding / "myac.ac")["freq"]
    assert np.asarray(freq.values).dtype == np.dtype("float64")
    assert isinstance(freq.values, np.ndarray)
    assert np.shape(freq.values) == (61,)


@pytest.mark.parametrize("encoding", ENCODINGS)
def test_ac_trace_is_a_complex_array(encoding):
    out = psf_parser.load(RUN / encoding / "myac.ac")["out"]
    assert isinstance(out.values, np.ndarray)
    assert np.asarray(out.values).dtype == np.dtype("complex128")
    assert np.shape(out.values) == (61,)


@pytest.mark.parametrize("encoding", ENCODINGS)
def test_windowed_transient_spans_its_blocks(encoding):
    file = psf_parser.load(RUN / encoding / "mytran.tran.tran")
    assert file.sweep is not None
    assert np.shape(file.sweep.values) == (653,)
    assert np.all(np.diff(file.sweep.values) > 0)
    assert all(np.shape(trace.values) == (653,) for trace in file.traces)


@pytest.mark.parametrize("encoding", ENCODINGS)
@pytest.mark.parametrize("name", ["myac.ac", "mytran.tran.tran", "myop.dc"])
def test_arrays_are_read_only_and_native(encoding, name):
    for variable in psf_parser.load(RUN / encoding / name):
        assert isinstance(variable.values, np.ndarray)
        assert variable.values.dtype.isnative
        with pytest.raises(ValueError, match="read-only"):
            variable.values[0] = 0


@pytest.mark.parametrize("encoding", ENCODINGS)
def test_entry_value_is_a_plain_python_number(encoding):
    out = psf_parser.load(RUN / encoding / "myop.dc")["out"]
    assert np.shape(out.values) == (1,)
    assert type(out.value) is float


def test_struct_entry_is_a_list_of_one_dict():
    entry = psf_parser.load(RUN / "ascii" / "logFile")["myac-ac"]
    assert type(entry.values) is list
    assert entry.value["dataFile"] == "myac.ac"


def test_value_on_a_column_raises():
    with pytest.raises(ValueError, match=r"use \.values"):
        _ = psf_parser.load(RUN / "binary" / "myac.ac")["out"].value


def _myac_rows() -> tuple[bytearray, int]:
    """The bytes of the binary `myac.ac`, and where its first tagged row starts."""
    data = bytearray((RUN / "binary" / "myac.ac").read_bytes())
    contents = struct.unpack("!I", data[-4:])[0]
    words = struct.unpack(f"!{(len(data) - 12 - contents) // 4}I", data[contents:-12])
    value_container = dict(zip(words[::2], words[1::2], strict=True))[4]
    return data, value_container + 8


def test_rows_in_a_different_order_fall_back_to_the_walk(tmp_path):
    """Each value stays with its own column, because its tag says which that is."""
    data, start = _myac_rows()
    float_cell, complex_cell = 16, 24
    row_two = start + float_cell + 2 * complex_cell + complex_cell
    in_cell = row_two + float_cell
    out_cell = in_cell + complex_cell
    data[in_cell : out_cell + complex_cell] = data[out_cell : out_cell + complex_cell] + data[in_cell:out_cell]
    path = tmp_path / "myac.ac"
    path.write_bytes(data)

    original = psf_parser.load(RUN / "binary" / "myac.ac")
    reordered = psf_parser.load(path)
    assert np.array_equal(reordered["out"].values, original["out"].values)
    assert np.array_equal(reordered["in"].values, original["in"].values)


def test_a_damaged_row_tag_raises(tmp_path):
    data, start = _myac_rows()
    row = 16 + 3 * 24  # the float sweep and three complex traces, each with an 8-byte tag
    data[start + 4 * row : start + 4 * row + 4] = bytes(4)
    path = tmp_path / "myac.ac"
    path.write_bytes(data)
    with pytest.raises(PsfParseError):
        psf_parser.load(path)


def test_a_windowed_column_of_another_type_raises(tmp_path):
    """No corpus file has one, so the reader refuses it rather than misreading it as float64."""
    data = (RUN / "binary" / "mytran.tran.tran").read_bytes()
    float_type = struct.pack("!I4sII", 1, b"V", 0, 11)
    assert float_type in data
    path = tmp_path / "mytran.tran.tran"
    path.write_bytes(data.replace(float_type, struct.pack("!I4sII", 1, b"V", 0, 12)))
    with pytest.raises(PsfParseError, match="windowed column"):
        psf_parser.load(path)
