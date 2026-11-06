"""A pure-Python parser for Cadence's PSF format."""

from pathlib import Path

from psf_parser._ascii.parser import AsciiParser
from psf_parser._binary.parser import BinaryParser
from psf_parser.errors import PsfParseError, PsfParserError, PsfStructureError
from psf_parser.model import Kind, PsfFile, PsfType, Role, Variable

__all__ = [
    "Kind",
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
    """Read a psfascii or psfbin file, detecting which from its contents.

    Args:
        path: A single PSF file, not a raw folder.

    Returns:
        The file's header, types and variables. The columns of a table are read on first access.

    Raises:
        PsfParseError: The file is not PSF, is truncated, or its declarations are malformed.
    """
    path = Path(path)
    with open(path, "rb") as handle:
        is_ascii = handle.read(len(ASCII_MAGIC)) == ASCII_MAGIC

    if is_ascii:
        return AsciiParser(path).read_schema()
    return BinaryParser(path).read_schema()
