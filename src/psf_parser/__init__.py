from psf_parser.file import PsfFile, Signal
from psf_parser.parser import PsfParser
from psf_parser.ascii.parser import PsfAsciiParser
from psf_parser.binary.parser import PsfBinParser

__all__ = ["PsfFile", "Signal", "PsfParser", "PsfAsciiParser", "PsfBinParser"]

try:
    from importlib.metadata import version
    __version__ = version("psf-parser")
except Exception:
    __version__ = "unknown"
