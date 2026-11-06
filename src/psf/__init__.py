"""A pure-Python parser for Cadence's PSF format."""

from pathlib import Path

from psf.ascii.parser import AsciiParser
from psf.binary.parser import BinaryParser
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
        return AsciiParser(path).parse()
    return BinaryParser(path).parse()
