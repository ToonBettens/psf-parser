"""The rules every parsed file must meet, whichever parser read it."""

from __future__ import annotations

from psf_parser.errors import PsfStructureError
from psf_parser.model import PsfFile, PsfType, Role, Variable


def add_type(file: PsfFile, type_: PsfType) -> None:
    """Add a type to the catalogue, raising if its name is taken."""
    if type_.name in file.types:
        raise PsfStructureError(f"duplicate type {type_.name!r}")
    file.types[type_.name] = type_


def add_variable(file: PsfFile, variable: Variable) -> Variable:
    """Add a variable to the file, raising if its name is taken."""
    if variable.name in file.variables:
        raise PsfStructureError(f"duplicate variable {variable.name!r} in section {variable.role.value}")
    file.variables[variable.name] = variable
    return variable


def check(file: PsfFile) -> None:
    """Raise if the sweep and trace columns differ in length, the usual sign of a desynchronised parser."""
    columns = [v for v in file if v.role is not Role.ENTRY]
    if len({len(v.values) for v in columns}) > 1:
        detail = ", ".join(f"{v.name}={len(v.values)}" for v in columns)
        raise PsfStructureError(f"columns have unequal lengths, so the value section desynchronised: {detail}")
