"""Values checked against what the circuit should do, because two encodings agreeing does not make them right."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

import psf_parser

RUN = Path(__file__).parent / "data" / "runs" / "rc_lowpass@23.1"
RESISTANCE = 1e3
CAPACITANCE = 1e-6


@pytest.mark.parametrize("encoding", ["ascii", "binary"])
def test_ac_response_is_that_of_the_rc_filter(encoding):
    file = psf_parser.load(RUN / encoding / "myac.ac")
    corner = 1 / (2 * math.pi * RESISTANCE * CAPACITANCE)
    expected = 1 / np.sqrt(1 + (np.asarray(file["freq"].values) / corner) ** 2)
    assert np.allclose(np.abs(file["out"].values), expected, rtol=1e-6)


@pytest.mark.parametrize("encoding", ["ascii", "binary"])
def test_operating_point_passes_the_source_through(encoding):
    file = psf_parser.load(RUN / encoding / "myop.dc")
    assert file["in"].value == pytest.approx(1)
    assert file["out"].value == pytest.approx(1)
    assert file["in"].units == "V"
