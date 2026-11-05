"""Construction of a `PsfFile`, with the invariants checked.

Both parsers build the same model, so the rules about what a valid file looks
like live here rather than being restated (and drifted) in each. The rules are
cheap to check and catch the failure mode that matters most for a format with no
specification: a parser that reads the wrong number of bytes does not raise, it
quietly produces a short column.
"""

from __future__ import annotations

from typing import Any

from psf.errors import PsfStructureError
from psf.model import Layout, Properties, PsfFile, PsfType, Role, Scalar, Variable


class PsfBuilder:
    """Accumulates a `PsfFile` as a parser reads.

    A parser calls `add_type` while reading TYPE, `declare` while reading SWEEP
    and TRACE, then `append`/`extend` as values arrive, and finally `build`.
    """

    def __init__(self, path: str | None = None):
        self.path = path
        self.header: dict[str, Scalar] = {}
        self.types: dict[str, PsfType] = {}
        self.variables: dict[str, Variable] = {}

    # --- schema -------------------------------------------------------------

    def add_header(self, key: str, value: Scalar) -> None:
        self.header[key] = value

    def add_type(self, type_: PsfType) -> PsfType:
        if type_.name in self.types:
            raise PsfStructureError(f"duplicate type {type_.name!r}")
        self.types[type_.name] = type_
        return type_

    def variable_named(self, name: str) -> Variable:
        """Resolve a variable reference, failing loudly on a value for a name never declared."""
        try:
            return self.variables[name]
        except KeyError:
            raise PsfStructureError(f"value for undeclared variable {name!r}") from None

    def type_named(self, name: str) -> PsfType:
        """Resolve a type reference, failing loudly if the file names one it never declared."""
        try:
            return self.types[name]
        except KeyError:
            raise PsfStructureError(f"undeclared type {name!r} referenced by a declaration") from None

    def declare(
        self,
        name: str,
        type_: PsfType | str,
        role: Role,
        properties: Properties | None = None,
    ) -> Variable:
        """Declare a variable. `type_` may be a `PsfType` or a name to resolve."""
        if name in self.variables:
            raise PsfStructureError(f"duplicate variable {name!r} in section {role.value}")
        resolved = self.type_named(type_) if isinstance(type_, str) else type_
        variable = Variable(name=name, type=resolved, role=role, properties=properties or {})
        self.variables[name] = variable
        return variable

    # --- data ---------------------------------------------------------------

    def append(self, name: str, value: Any) -> None:
        """Append one value to a declared variable's column."""
        try:
            self.variables[name].values.append(value)
        except KeyError:
            raise PsfStructureError(f"value for undeclared variable {name!r}") from None

    def extend(self, name: str, values: list[Any]) -> None:
        """Append many values at once, as the windowed binary layout produces them."""
        try:
            self.variables[name].values.extend(values)
        except KeyError:
            raise PsfStructureError(f"values for undeclared variable {name!r}") from None

    def add_value(
        self,
        name: str,
        type_: PsfType | str,
        value: Any,
        properties: Properties | None = None,
    ) -> Variable:
        """Declare and populate a single-valued variable, for files with no sweep."""
        variable = self.declare(name, type_, Role.ENTRY, properties)
        variable.values.append(value)
        return variable

    # --- finish -------------------------------------------------------------

    def build(self) -> PsfFile:
        """Validate, decide the file's layout, and return it."""
        self._check_columns_aligned()
        return PsfFile(
            header=self.header,
            types=self.types,
            variables=self.variables,
            layout=self._layout(),
            path=self.path,
        )

    def _layout(self) -> Layout:
        if any(v.role is Role.SWEEP for v in self.variables.values()):
            return Layout.SWEPT
        return Layout.RECORD if self.variables else Layout.EMPTY

    def _check_columns_aligned(self) -> None:
        """A swept file is a table: every sweep and trace column has the same length.

        This is the check worth having. A parser that misreads a value section
        does not usually crash -- it desynchronises and produces columns of
        different lengths, which without this check reaches the user as
        plausible-looking data.
        """
        columns = [s for s in self.variables.values() if s.role in (Role.SWEEP, Role.TRACE)]
        lengths = {len(s.values) for s in columns}
        if len(lengths) > 1:
            detail = ", ".join(f"{s.name}={len(s.values)}" for s in columns)
            raise PsfStructureError(f"columns have unequal lengths, so the value section desynchronised: {detail}")
