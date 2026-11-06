"""Exceptions raised while reading PSF files.

Everything raised about a *file* derives from `PsfParserError`, so a caller
walking a directory can write one `except` and not track our internals:

    try:
        psf_parser.load(path)
    except psf_parser.PsfParserError:
        ...

Errors about how the API was *used* -- a missing variable name, `.value` on a
multi-valued column -- stay as the standard `KeyError` and `ValueError`, because
those follow Python semantics a caller already knows.
"""


class PsfParserError(Exception):
    """Base class for every error this package raises about a file."""


class PsfParseError(PsfParserError, ValueError):
    """A file could not be read: malformed, truncated, or not PSF at all.

    Also a `ValueError`, following `json.JSONDecodeError` and
    `tomllib.TOMLDecodeError`, so stdlib-shaped handling works without knowing
    this hierarchy.
    """


class PsfStructureError(PsfParserError):
    """A file parsed, but the result violates an invariant the model relies on.

    Kept distinct from `PsfParseError` because the two point at different
    culprits: a parse error means the file is bad, while a structure error
    almost always means a parser desynchronised -- reading the wrong number of
    bytes rarely raises, it just produces columns of unequal length. For a
    format with no published specification, that is the difference between a
    user's broken file and a bug report against this package.
    """
