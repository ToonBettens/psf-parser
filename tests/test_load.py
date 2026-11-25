"""Every file in the corpus loads through `psf_parser`, and both encodings of a simulation agree."""

from __future__ import annotations

import re
import struct
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import psf_parser
from psf_parser._binary.parser import ValueSection
from psf_parser.model import Role

# psfascii holds only the digits it writes. That is `precision`, except in files where Spectre
# ignores it (format-notes 2.1). Only seventeen digits round-trip a float64: the default
# precision of 25.1 writes sixteen.
FULL_PRECISION_DIGITS = 17
SIX_DIGITS_TOLERANCE = 1e-5
QUOTED = re.compile(r'"[^"]*"')
NUMBER = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


def _significant_digits(number: str) -> int:
    mantissa = re.split("[eE]", number)[0].lstrip("+-").replace(".", "").lstrip("0")
    return len(mantissa)


def _digits_written(path: Path) -> dict[str, int]:
    """For each variable, the most significant digits of its numbers in a psfascii value section.

    A quoted name outside any parentheses begins a variable's value, and other lines continue
    it. Columns of one file can differ: a sweep at full precision, traces at six digits.
    """
    text = path.read_text(errors="replace")
    digits: dict[str, int] = {}
    name = None
    depth = 0
    for line in text[text.find("\nVALUE\n") :].splitlines()[2:]:
        if depth == 0 and line.startswith('"'):
            name = line[1 : line.index('"', 1)]
        unquoted = QUOTED.sub(" ", line)
        depth += unquoted.count("(") - unquoted.count(")")
        if name is None:
            continue
        numbers = NUMBER.findall(unquoted)
        digits[name] = max([digits.get(name, 0), *(_significant_digits(number) for number in numbers)])
    return digits


def _tolerance(digits: int) -> float:
    """Exact for values written at full precision, otherwise as loose as their digits require."""
    if digits >= FULL_PRECISION_DIGITS:
        return 0.0
    return 10.0 ** (1 - max(digits, 6))


def _same(a: Any, b: Any, tolerance: float = 0.0) -> bool:
    """Equal to within a relative tolerance, where NaN equals NaN and a value's type has to match too."""
    if type(a) is not type(b):
        return False
    if isinstance(a, np.ndarray):
        return a.dtype == b.dtype and np.allclose(a, b, rtol=tolerance, atol=0.0, equal_nan=True)
    if isinstance(a, float | complex):
        return bool(np.isclose(a, b, rtol=tolerance, atol=0.0, equal_nan=True))
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(_same(a[key], b[key], tolerance) for key in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(_same(x, y, tolerance) for x, y in zip(a, b, strict=True))
    return a == b


def test_sample_loads(sample):
    file = psf_parser.load(sample.path)
    assert isinstance(file, psf_parser.PsfFile)
    traces = [variable for variable in file if variable.role is Role.TRACE]
    # A paramset sweep's parent declares its traces but writes none (format-notes 1.2).
    traces_written = not traces or any(len(variable.values) > 0 for variable in traces)
    for variable in file:
        if variable.role is Role.TRACE and not traces_written:
            continue
        assert len(variable.values) > 0, variable.name


def test_run_has_metadata(run):
    assert run.meta.get("psfversion"), f"{run.name}/run.toml is missing psfversion"
    assert run.formats, f"{run.name} contains no format directories"


def test_encodings_agree(pair):
    ascii_sample, binary_sample = pair
    digits = _digits_written(ascii_sample.path)
    from_ascii, from_binary = psf_parser.load(ascii_sample.path), psf_parser.load(binary_sample.path)

    assert list(from_ascii.variables) == list(from_binary.variables)
    assert set(from_ascii.types) == set(from_binary.types)
    for name, ascii_variable in from_ascii.variables.items():
        binary_variable = from_binary[name]
        assert ascii_variable.role is binary_variable.role, name
        assert ascii_variable.type.kind is binary_variable.type.kind, name
        assert ascii_variable.units == binary_variable.units, name
        assert ascii_variable.properties == binary_variable.properties, name
        tolerance = _tolerance(digits.get(name, FULL_PRECISION_DIGITS))
        assert _same(ascii_variable.values, binary_variable.values, tolerance), name


def test_corpus_covers_every_value_layout(every_sample):
    """Guards the coverage above: removing the last file of a layout must not pass unnoticed."""
    found = set()
    for sample in every_sample:
        data = sample.path.read_bytes()
        # The logFile and some info files are psfascii whatever -format says (format-notes 4).
        if sample.format == "binary" and not data.startswith(b"HEADER"):
            found.add(ValueSection(struct.unpack("!I", data[:4])[0]))
    assert found == set(ValueSection)


def test_comparison_is_exact_unless_given_a_tolerance():
    assert _same(np.array([1.0, np.nan]), np.array([1.0, np.nan]))
    assert not _same(np.array([1.0]), np.array([1.0 + 1e-15]))
    assert _same(np.array([1.0]), np.array([1.000001]), SIX_DIGITS_TOLERANCE)
    assert not _same(np.array([1.0]), np.array([1.001]), SIX_DIGITS_TOLERANCE)
    assert _same(1 + 2j, 1 + 2j)
    assert not _same(1.0, 1)


def test_digits_are_counted_per_variable(tmp_path):
    path = tmp_path / "x.ac"
    path.write_text(
        'HEADER\nVALUE\n"freq" 3.1622776601683795\n"out" (0.999014 -0.0313850)\n'
        '"mysweep-001" 2\n"s" "subckt" (\n"a b"\n12.5\n)\nEND\n'
    )
    assert _digits_written(path) == {"freq": 17, "out": 6, "mysweep-001": 1, "s": 3}


@pytest.mark.parametrize(("digits", "expected"), [(17, 0.0), (16, 1e-15), (10, 1e-9), (6, 1e-5), (1, 1e-5)])
def test_tolerance_follows_the_digits_written(digits, expected):
    assert _tolerance(digits) == pytest.approx(expected)
