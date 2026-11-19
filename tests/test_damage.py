"""Damaged files raise only `PsfParserError`, and the rules on row counts and integers hold."""

from __future__ import annotations

import io
import random
import struct
from pathlib import Path

import pytest

import psf_parser
from psf_parser._binary.parser import BinaryParser
from psf_parser._binary.reader import BinaryReader
from psf_parser._columns import as_column
from psf_parser.errors import PsfParseError, PsfStructureError
from psf_parser.model import Kind, PsfType

RUN = Path(__file__).parent / "data" / "runs" / "rc_lowpass@23.1"
ROUNDS = 300


def _damage(data: bytes, rng: random.Random) -> bytes:
    damaged = bytearray(data)
    match rng.choice(["flip", "cut", "zero"]):
        case "flip":
            for _ in range(4):
                damaged[rng.randrange(len(damaged))] = rng.randrange(256)
        case "cut":
            del damaged[rng.randrange(len(damaged)) :]
        case "zero":
            at = rng.randrange(len(damaged))
            damaged[at : at + 16] = bytes(len(damaged[at : at + 16]))
    return bytes(damaged)


@pytest.mark.parametrize("encoding", ["ascii", "binary"])
def test_damaged_files_raise_only_psf_parser_error(encoding, tmp_path):
    """A damaged file may also read without complaint: a changed byte in a number cannot be detected."""
    sources = [p.read_bytes() for p in sorted((RUN / encoding).iterdir())]
    rng = random.Random(1)
    path = tmp_path / "damaged"
    for _ in range(ROUNDS):
        path.write_bytes(_damage(rng.choice(sources), rng))
        try:
            for variable in psf_parser.load(path):
                _ = variable.values
        except psf_parser.PsfParserError:
            pass


@pytest.mark.parametrize("name", ["myac.ac", "mytran.tran.tran"])
def test_a_wrong_row_count_in_the_header_raises(name, tmp_path):
    data = (RUN / "binary" / name).read_bytes()
    file = psf_parser.load(RUN / "binary" / name)
    points = len(file["out"].values)
    key = b"PSF sweep points"
    entry = struct.pack("!II", 34, len(key)) + key + bytes(-len(key) % 4) + struct.pack("!i", points)
    assert entry in data
    path = tmp_path / name
    path.write_bytes(data.replace(entry, entry[:-4] + struct.pack("!i", points + 1)))
    with pytest.raises(PsfStructureError, match="PSF sweep points"):
        _ = psf_parser.load(path)["out"].values


def test_a_windowed_block_with_too_many_values_raises(tmp_path):
    data = bytearray((RUN / "binary" / "mytran.tran.tran").read_bytes())
    first_block = 4096
    data[first_block + 6 : first_block + 8] = struct.pack("!H", 512)
    path = tmp_path / "mytran.tran.tran"
    path.write_bytes(data)
    with pytest.raises(PsfParseError, match="slots"):
        _ = psf_parser.load(path)["out"].values


def test_something_that_is_not_psf_names_psfxl(tmp_path):
    path = tmp_path / "out.tran"
    path.write_bytes(bytes(100))
    with pytest.raises(PsfParseError, match="psfxl is not supported"):
        psf_parser.load(path)


def test_a_numeric_value_that_does_not_fit_raises():
    with pytest.raises(PsfParseError, match="does not fit"):
        as_column(Kind.INT8, [999])


def _reader(data: bytes) -> BinaryReader:
    return BinaryReader(io.BufferedReader(io.BytesIO(data)))


def test_int32_values_are_signed():
    parser = BinaryParser("unused")
    parser.reader = _reader(struct.pack("!i", -1))
    assert parser._read_value(PsfType("n", Kind.INT32)) == -1


def test_int_properties_are_signed(tmp_path):
    data = (RUN / "binary" / "myac.ac").read_bytes()
    file = psf_parser.load(RUN / "binary" / "myac.ac")
    key = b"PSF traces"
    entry = struct.pack("!II", 34, len(key)) + key + bytes(-len(key) % 4) + struct.pack("!i", file.header["PSF traces"])
    assert entry in data
    path = tmp_path / "myac.ac"
    path.write_bytes(data.replace(entry, entry[:-4] + struct.pack("!i", -1)))
    assert psf_parser.load(path).header["PSF traces"] == -1


def test_padding_after_the_magic_is_accepted(tmp_path):
    """Spectre 25.1 pads windowed files past their table of contents."""
    data = (RUN / "binary" / "mytran.tran.tran").read_bytes()
    path = tmp_path / "mytran.tran.tran"
    path.write_bytes(data + b"\xff\xff\xff\xff\x7f\xff\xff\xff" * 2048)
    assert len(psf_parser.load(path)["out"].values) == 653


def test_the_magic_is_only_searched_for_near_the_end(tmp_path):
    data = (RUN / "binary" / "mytran.tran.tran").read_bytes()
    path = tmp_path / "mytran.tran.tran"
    path.write_bytes(data + bytes(2 << 20))
    with pytest.raises(PsfParseError, match="truncated"):
        psf_parser.load(path)


def test_a_string_type_with_code_14_has_one_extra_word():
    name = b"state\0\0\0"
    declaration = struct.pack("!III", 16, 7, 5) + name + struct.pack("!III", 0, 14, 0)
    parser = BinaryParser("unused")
    parser.reader = _reader(declaration + struct.pack("!I", 19))
    assert parser._read_type().kind is Kind.STRING
    assert parser.reader.read_uint32() == 19
