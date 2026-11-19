"""Every file in the corpus loads through `psf_parser`, and both encodings of a simulation agree."""

from __future__ import annotations

import struct
from typing import Any

import numpy as np

import psf_parser
from psf_parser._binary.parser import ValueSection

# Spectre's default precision writes six significant digits to psfascii, and qpss frequency
# index files always do (format-notes 2.1).
SIX_DIGITS_TOLERANCE = 1e-5


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
    for variable in file:
        assert len(variable.values) > 0


def test_run_has_metadata(run):
    assert run.meta.get("psfversion"), f"{run.name}/run.toml is missing psfversion"
    assert run.formats, f"{run.name} contains no format directories"


def test_encodings_agree(pair):
    ascii_sample, binary_sample = pair
    six_digits = ascii_sample.run.startswith("default_precision") or ascii_sample.path.name.endswith(".fi.qpss")
    tolerance = SIX_DIGITS_TOLERANCE if six_digits else 0.0
    from_ascii, from_binary = psf_parser.load(ascii_sample.path), psf_parser.load(binary_sample.path)

    assert list(from_ascii.variables) == list(from_binary.variables)
    assert set(from_ascii.types) == set(from_binary.types)
    for name, ascii_variable in from_ascii.variables.items():
        binary_variable = from_binary[name]
        assert ascii_variable.role is binary_variable.role, name
        assert ascii_variable.type.kind is binary_variable.type.kind, name
        assert ascii_variable.units == binary_variable.units, name
        assert ascii_variable.properties == binary_variable.properties, name
        assert _same(ascii_variable.values, binary_variable.values, tolerance), name


def test_corpus_covers_every_value_layout(every_sample):
    """Guards the coverage above: removing the last file of a layout must not pass unnoticed."""
    found = set()
    for sample in every_sample:
        if sample.format == "binary" and sample.path.name != "logFile":
            found.add(ValueSection(struct.unpack("!I", sample.path.read_bytes()[:4])[0]))
    assert found == set(ValueSection)


def test_comparison_is_exact_unless_given_a_tolerance():
    assert _same(np.array([1.0, np.nan]), np.array([1.0, np.nan]))
    assert not _same(np.array([1.0]), np.array([1.0 + 1e-15]))
    assert _same(np.array([1.0]), np.array([1.000001]), SIX_DIGITS_TOLERANCE)
    assert not _same(np.array([1.0]), np.array([1.001]), SIX_DIGITS_TOLERANCE)
    assert _same(1 + 2j, 1 + 2j)
    assert not _same(1.0, 1)
