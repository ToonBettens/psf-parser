from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

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

    def __repr__(self) -> str:
        detail = f" of {self.element.name}" if self.element else ""
        if self.fields:
            detail = f"({', '.join(f.name for f in self.fields)})"
        return f"<PsfType {self.name}: {self.kind.value}{detail}>"


class Variable:
    """One named quantity within a file, with the type that describes it.

    Attributes:
        name: Name as declared.
        type: The type this variable was declared with.
        role: Part this variable plays in its file.
        properties: Annotations on the declaration itself, verbatim.
    """

    def __init__(
        self,
        name: str,
        type: PsfType,
        role: Role,
        properties: Properties | None = None,
        values: np.ndarray | list[Any] | None = None,
    ):
        self.name = name
        self.type = type
        self.role = role
        self.properties = properties if properties is not None else {}
        self._values = values
        self._source: Callable[[], None] | None = None

    @property
    def values(self) -> np.ndarray | list[Any]:
        """The data in file order, read from disk on first access.

        Returns:
            A read-only array in native byte order for numeric kinds, and a list for any other.

        Raises:
            PsfParseError: The value section is damaged, or the file changed after it was loaded.
            PsfStructureError: The columns came out with unequal lengths.
        """
        if self._values is None:
            if self._source is None:
                return []
            self._source()
        return self._values if self._values is not None else []

    @property
    def units(self) -> str | None:
        own = self.properties.get("units")
        return str(own) if own else self.type.units

    @property
    def value(self) -> Any:
        if len(self.values) != 1:
            raise ValueError(f"{self.name!r} holds {len(self.values)} values; use .values")
        value = self.values[0]
        return value.item() if isinstance(value, np.generic) else value

    def __repr__(self) -> str:
        units = f" [{self.units}]" if self.units else ""
        count = f"{len(self._values)}x " if self._values is not None else ""
        return f"<Variable {self.name}{units}: {count}{self.type.kind.value}>"


@dataclass(eq=False)
class PsfFile:
    """A parsed PSF file.

    Attributes:
        header: Flat metadata from the HEADER section.
        types: The type catalogue.
        variables: Every declared variable, in file order.
        path: Where it was read from, if it came from disk.
    """

    header: dict[str, Scalar] = field(default_factory=dict)
    types: dict[str, PsfType] = field(default_factory=dict)
    variables: dict[str, Variable] = field(default_factory=dict)
    path: str | None = None

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

    def __repr__(self) -> str:
        name = f" {self.path}" if self.path else ""
        return f"<PsfFile{name}: {len(self.variables)} variables>"
