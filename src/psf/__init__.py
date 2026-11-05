"""A pure-Python parser for Cadence's PSF format."""

from pathlib import Path

from psf.errors import PsfParseError, PsfParserError, PsfStructureError
from psf.model import Kind, Layout, PsfFile, PsfType, Role, Variable

__all__ = [
    "Kind",
    "Layout",
    "PsfFile",
    "PsfParseError",
    "PsfParserError",
    "PsfStructureError",
    "PsfType",
    "Role",
    "Variable",
    "load",
]

ASCII_MAGIC = b"HEADER"


def load(path: str | Path) -> PsfFile:
    """Parse a PSF file, detecting whether it is psfascii or psfbin."""
    path = Path(path)
    with open(path, "rb") as handle:
        is_ascii = handle.read(len(ASCII_MAGIC)) == ASCII_MAGIC

    if is_ascii:
        from psf.ascii.parser import AsciiParser

        return AsciiParser(path).parse()

    from psf.binary.parser import BinaryParser

    return BinaryParser(path).parse()
