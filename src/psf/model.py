from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

Scalar = int | float | complex | str
Properties = Mapping[str, Scalar]


class Kind(Enum):
    """What a type is, independent of how a format spells it."""

    INT8 = "int8"
    INT32 = "int32"
    FLOAT64 = "float64"
    COMPLEX = "complex"
    STRING = "string"
    ARRAY = "array"
    STRUCT = "struct"

    @property
    def is_scalar(self) -> bool:
        return self not in (Kind.ARRAY, Kind.STRUCT)


class Role(Enum):
    """The part a variable plays in its file."""

    SWEEP = "sweep"  # It is the independent variable.
    TRACE = "trace"  # It is a dependent variable.
    ENTRY = "entry"  # Datapoint, there is no sweep at all.


class Layout(Enum):
    """How a file arranges its values."""

    EMPTY = "empty"  # Header only
    RECORD = "record"  # Independently typed named entries, no sweep.
    SWEPT = "swept"  # A table of equal-length columns, with or without traces.


@dataclass(frozen=True)
class PsfType:
    """A named type from the TYPE section.

    Attributes:
        name: Name of the type as declared.
        kind: What the type is.
        properties: Annotations from the declaration.
        element: Element type, for `Kind.ARRAY`.
        fields: Member types in declared order, for `Kind.STRUCT`.
    """

    name: str
    kind: Kind
    properties: Properties = field(default_factory=dict)
    element: PsfType | None = None
    fields: tuple[PsfType, ...] = ()

    @property
    def units(self) -> str | None:
        value = self.properties.get("units")
        return str(value) if value else None

    def field_named(self, name: str) -> PsfType | None:
        return next((f for f in self.fields if f.name == name), None)

    def __repr__(self) -> str:
        detail = f" of {self.element.name}" if self.element else ""
        if self.fields:
            detail = f"({', '.join(f.name for f in self.fields)})"
        return f"<PsfType {self.name}: {self.kind.value}{detail}>"


@dataclass
class Variable:
    """One named quantity within a file, with the type that describes it.

    Attributes:
        name: Name as declared.
        type: The type this variable was declared with.
        role: Part this variable plays in its file.
        properties: Annotations on the declaration itself, verbatim.
        values: The data, in file order.
    """

    name: str
    type: PsfType
    role: Role
    properties: Properties = field(default_factory=dict)
    values: list[Any] = field(default_factory=list)

    @property
    def units(self) -> str | None:
        own = self.properties.get("units")
        return str(own) if own else self.type.units

    @property
    def value(self) -> Any:
        if len(self.values) != 1:
            raise ValueError(f"{self.name!r} holds {len(self.values)} values; use .values")
        return self.values[0]

    def __repr__(self) -> str:
        units = f" [{self.units}]" if self.units else ""
        return f"<Variable {self.name}{units}: {len(self.values)}x {self.type.kind.value}>"


@dataclass
class PsfFile:
    """A parsed PSF file.

    Attributes:
        header: Flat metadata from the HEADER section.
        types: The type catalogue.
        variables: Every declared variable, in file order.
        layout: How this file arranges its values.
        path: Where it was read from, if it came from disk.
    """

    header: dict[str, Scalar] = field(default_factory=dict)
    types: dict[str, PsfType] = field(default_factory=dict)
    variables: dict[str, Variable] = field(default_factory=dict)
    layout: Layout = Layout.EMPTY
    path: str | None = None

    @property
    def is_swept(self) -> bool:
        return self.layout is Layout.SWEPT

    @property
    def sweep(self) -> Variable | None:
        """The innermost axis, or None for files that are not swept."""
        return next((v for v in self.variables.values() if v.role is Role.SWEEP), None)

    @property
    def traces(self) -> list[Variable]:
        """Variables that depend on the sweep."""
        return [v for v in self.variables.values() if v.role is Role.TRACE]

    @property
    def entries(self) -> list[Variable]:
        """Standalone entries, from a file with no sweep."""
        return [v for v in self.variables.values() if v.role is Role.ENTRY]

    def __getitem__(self, name: str) -> Variable:
        try:
            return self.variables[name]
        except KeyError:
            raise KeyError(f"no variable {name!r}; available: {', '.join(self.variables)[:120]}") from None

    def __contains__(self, name: str) -> bool:
        return name in self.variables

    def __iter__(self) -> Iterator[Variable]:
        return iter(self.variables.values())

    def __len__(self) -> int:
        return len(self.variables)

    def rows(self) -> Iterator[tuple]:
        """Iterate the table row by row, sweep column first."""
        columns = ([self.sweep] if self.sweep else []) + self.traces
        yield from zip(*(c.values for c in columns), strict=True)

    def __repr__(self) -> str:
        sweep = self.sweep
        what = f"{len(sweep.values)} points" if sweep else f"{len(self.variables)} entries"
        name = f" {self.path}" if self.path else ""
        return f"<PsfFile{name}: {self.layout.value}, {what}, {len(self.variables)} variables>"
