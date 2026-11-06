"""Every file in the corpus loads through `psf_parser`, and both encodings of a simulation agree."""

from __future__ import annotations

import math
import struct
from typing import Any

import numpy as np

import psf_parser
from psf_parser._binary.parser import ValueSection


def _same(a: Any, b: Any) -> bool:
    """Exact equality, except that NaN equals NaN and a value's type has to match too."""
    if type(a) is not type(b):
        return False
    if isinstance(a, np.ndarray):
        return a.dtype == b.dtype and np.array_equal(a, b, equal_nan=True)
    if isinstance(a, float):
        return a == b or (math.isnan(a) and math.isnan(b))
    if isinstance(a, complex):
        return _same(a.real, b.real) and _same(a.imag, b.imag)
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(_same(a[key], b[key]) for key in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b, strict=True))
    return a == b


def test_sample_loads(sample):
    assert isinstance(psf_parser.load(sample.path), psf_parser.PsfFile)


def test_run_has_metadata(run):
    assert run.meta.get("psfversion"), f"{run.name}/run.toml is missing psfversion"
    assert run.formats, f"{run.name} contains no format directories"


def test_encodings_agree(pair):
    ascii_sample, binary_sample = pair
    from_ascii, from_binary = psf_parser.load(ascii_sample.path), psf_parser.load(binary_sample.path)

    assert list(from_ascii.variables) == list(from_binary.variables)
    assert set(from_ascii.types) == set(from_binary.types)
    for name, ascii_variable in from_ascii.variables.items():
        binary_variable = from_binary[name]
        assert ascii_variable.role is binary_variable.role, name
        assert ascii_variable.type.kind is binary_variable.type.kind, name
        assert ascii_variable.units == binary_variable.units, name
        assert ascii_variable.properties == binary_variable.properties, name
        assert _same(ascii_variable.values, binary_variable.values), name


def test_corpus_covers_every_value_layout(run):
    """Guards the coverage above: removing the last file of a layout must not pass unnoticed."""
    found = set()
    for sample in run.samples("binary"):
        if sample.path.name != "logFile":
            found.add(ValueSection(struct.unpack("!I", sample.path.read_bytes()[:4])[0]))
    assert found == set(ValueSection)
