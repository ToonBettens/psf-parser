"""A truncated file must fail, not parse into short columns.

This is the failure mode that matters for a format with no specification. A
parser that runs out of input does not usually produce nonsense -- it produces
plausible data with rows missing, which reaches the caller looking correct.

The regression these guard: `Tokenizer.__bool__` used to let the section loops
exit at end-of-input instead of raising, so a psfascii file with its END clause
removed parsed happily and returned however many rows it had reached.
"""

from __future__ import annotations

import pytest

import psf_parser
from psf_parser.errors import PsfParseError


def test_missing_end_raises(ascii_sample, tmp_path):
    """Drop the END clause, keeping every data row intact.

    The sharp case: the file stays internally consistent, so a column-alignment
    check cannot catch it. Only running out of input can.
    """
    text = ascii_sample.path.read_text()
    if "\nEND" not in text:
        pytest.skip("no END clause to remove")

    truncated = tmp_path / ascii_sample.path.name
    truncated.write_text(text[: text.rindex("\nEND")])

    with pytest.raises(PsfParseError):
        psf_parser.load(truncated)


def test_cut_in_half_raises(ascii_sample, tmp_path):
    """Cut mid-file, which may also land mid-row or mid-declaration."""
    text = ascii_sample.path.read_text()
    truncated = tmp_path / ascii_sample.path.name
    truncated.write_text(text[: len(text) // 2])

    with pytest.raises(PsfParseError):
        psf_parser.load(truncated)


def test_intact_file_still_parses(ascii_sample):
    """The other half of the property: nothing above rejects a whole file."""
    assert psf_parser.load(ascii_sample.path) is not None
