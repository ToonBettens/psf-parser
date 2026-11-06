"""Exceptions raised about PSF files. Misuse of the API raises the standard `KeyError` and `ValueError`."""


class PsfParserError(Exception):
    """Base class for every error this package raises about a file."""


class PsfParseError(PsfParserError, ValueError):
    """A file could not be read: malformed, truncated or not PSF at all."""


class PsfStructureError(PsfParserError):
    """A file parsed, but the result breaks a model invariant."""
