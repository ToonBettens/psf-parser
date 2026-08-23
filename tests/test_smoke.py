"""Every file in the corpus must parse.

The cheapest possible signal, and the one that catches outright breakage. It
uses the PsfParser factory rather than a format-specific parser so that format
detection is exercised too -- which matters for logFile, psfascii even inside a
psfbin run.
"""

from psf_parser import PsfParser


def test_parses(sample):
    parser = PsfParser(sample.path).parse()
    assert isinstance(parser.header, dict)


def test_run_has_metadata(run):
    assert run.meta.get("psfversion"), f"{run.name}/run.toml is missing psfversion"
    assert run.formats, f"{run.name} contains no format directories"
