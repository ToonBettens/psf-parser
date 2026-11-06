"""`load` reads declarations only, and values arrive on first access."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import numpy as np
import pytest

import psf_parser
from psf_parser._binary.reader import BinaryReader
from psf_parser.errors import PsfParseError, PsfStructureError

RUN = Path(__file__).parent / "data" / "runs" / "rc_lowpass@1.4.0"
TABLES = [("ascii", "myac.ac"), ("binary", "myac.ac"), ("ascii", "mytran.tran.tran"), ("binary", "mytran.tran.tran")]


def _copy(encoding: str, name: str, tmp_path: Path) -> Path:
    return Path(shutil.copy(RUN / encoding / name, tmp_path / name))


@pytest.mark.parametrize(("encoding", "name"), TABLES)
def test_load_reads_no_table_values(encoding, name):
    file = psf_parser.load(RUN / encoding / name)
    assert file.header
    assert file.sweep is not None
    assert file.sweep.units
    assert len(file) == 4
    assert "points" not in repr(file)
    assert repr(file["out"])
    assert all(variable._values is None for variable in file)


@pytest.mark.parametrize(("encoding", "name"), TABLES)
def test_first_access_reads_and_caches(encoding, name):
    file = psf_parser.load(RUN / encoding / name)
    first = file["out"].values
    assert file["out"].values is first
    assert "x" in repr(file["out"])


@pytest.mark.parametrize("encoding", ["ascii", "binary"])
def test_named_entries_are_read_at_load(encoding):
    file = psf_parser.load(RUN / encoding / "myop.dc")
    assert all(variable._values is not None for variable in file)


@pytest.mark.parametrize(("encoding", "name"), TABLES)
def test_changed_file_raises_on_first_access(encoding, name, tmp_path):
    path = _copy(encoding, name, tmp_path)
    file = psf_parser.load(path)
    with path.open("ab") as handle:
        handle.write(b"\n")
    with pytest.raises(PsfParseError, match="changed"):
        _ = file["out"].values


@pytest.mark.parametrize("encoding", ["ascii", "binary"])
def test_same_size_with_a_new_time_raises(encoding, tmp_path):
    path = _copy(encoding, "myac.ac", tmp_path)
    file = psf_parser.load(path)
    status = path.stat()
    os.utime(path, ns=(status.st_atime_ns, status.st_mtime_ns + 1))
    with pytest.raises(PsfParseError, match="changed"):
        _ = file["out"].values


@pytest.mark.parametrize("encoding", ["ascii", "binary"])
def test_deleted_file_raises_on_first_access(encoding, tmp_path):
    path = _copy(encoding, "myac.ac", tmp_path)
    file = psf_parser.load(path)
    path.unlink()
    with pytest.raises(PsfParseError, match="changed"):
        _ = file["out"].values


def test_damaged_ascii_values_load_and_raise_on_access(tmp_path):
    path = _copy("ascii", "myac.ac", tmp_path)
    text = path.read_text()
    at = text.index('"out" (', text.index("\nVALUE\n"))
    path.write_text(text[:at] + '"out" ?' + text[at + 7 :])
    file = psf_parser.load(path)
    assert file["out"].units
    with pytest.raises(PsfParseError):
        _ = file["out"].values


def test_short_columns_are_not_kept_after_the_check_fails(tmp_path):
    """A second access must raise again, and never hand back the short columns."""
    path = _copy("ascii", "myac.ac", tmp_path)
    text = path.read_text()
    at = text.index('"out" (', text.index("\nVALUE\n"))
    path.write_text(text[:at] + text[text.index("\n", at) + 1 :])
    file = psf_parser.load(path)
    for _ in range(2):
        with pytest.raises(PsfStructureError):
            _ = file["freq"].values


def test_value_not_on_its_own_line_raises(tmp_path):
    path = _copy("ascii", "myac.ac", tmp_path)
    path.write_text(path.read_text().replace("\nVALUE\n", "\nVALUE ", 1))
    with pytest.raises(PsfParseError, match="line of its own"):
        psf_parser.load(path)


def test_an_error_line_counts_from_the_top_of_the_file(tmp_path):
    path = _copy("ascii", "myac.ac", tmp_path)
    text = path.read_text()
    at = text.index('"out" (', text.index("\nVALUE\n"))
    path.write_text(text[:at] + '"out" ?' + text[at + 7 :])
    expected = text[:at].count("\n") + 1
    file = psf_parser.load(path)
    with pytest.raises(PsfParseError, match=f"line {expected},"):
        _ = file["out"].values


def test_windowed_read_leaves_the_other_columns_unread():
    file = psf_parser.load(RUN / "binary" / "mytran.tran.tran")
    _ = file["out"].values
    assert file["out"]._values is not None
    assert all(variable._values is None for variable in file if variable.name != "out")


def test_windowed_read_does_not_touch_the_other_columns_on_disk(monkeypatch):
    file = psf_parser.load(RUN / "binary" / "mytran.tran.tran")
    read = []
    original = BinaryReader.read_bytes

    def counting(self, n):
        read.append(n)
        return original(self, n)

    monkeypatch.setattr(BinaryReader, "read_bytes", counting)
    assert len(file["out"].values) == 653
    assert sum(read) < 653 * 8 * 2


@pytest.mark.parametrize("name", ["time", "in", "out", "Vin:p"])
def test_each_windowed_column_matches_its_ascii_column(name):
    binary = psf_parser.load(RUN / "binary" / "mytran.tran.tran")[name].values
    assert np.array_equal(binary, psf_parser.load(RUN / "ascii" / "mytran.tran.tran")[name].values)


def test_windowed_columns_read_after_a_change_raise_but_read_ones_stay(tmp_path):
    path = _copy("binary", "mytran.tran.tran", tmp_path)
    file = psf_parser.load(path)
    out = file["out"].values
    with path.open("ab") as handle:
        handle.write(b"\0")
    assert file["out"].values is out
    with pytest.raises(PsfParseError, match="changed"):
        _ = file["in"].values


@pytest.mark.parametrize(
    ("encoding", "name"), [("binary", "myac.ac"), ("ascii", "myac.ac"), ("ascii", "mytran.tran.tran")]
)
def test_tagged_and_ascii_reads_keep_every_column(encoding, name):
    file = psf_parser.load(RUN / encoding / name)
    _ = file["out"].values
    assert all(variable._values is not None for variable in file)
