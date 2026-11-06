"""Conversion of parsed values into what `Variable.values` holds."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

from psf_parser.model import Kind, PsfFile, Role

NUMERIC_DTYPES = {
    Kind.INT8: np.int8,
    Kind.INT32: np.int32,
    Kind.FLOAT64: np.float64,
    Kind.COMPLEX: np.complex128,
}


def as_column(kind: Kind, values: Any) -> np.ndarray | list[Any]:
    """A read-only array in native byte order for a numeric kind, and a list for any other."""
    dtype = NUMERIC_DTYPES.get(kind)
    if dtype is None:
        return list(values)
    column = np.asarray(values, dtype=dtype)
    column.setflags(write=False)
    return column


def assign_columns(file: PsfFile, columns: Mapping[str, Any]) -> None:
    """Give every sweep and trace its column, which is empty when no values were read."""
    for variable in file:
        if variable.role is not Role.ENTRY:
            variable.values = as_column(variable.type.kind, columns.get(variable.name, []))
