"""Conversion of parsed values into what `Variable.values` holds, and reading them on first access."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from functools import partial
from pathlib import Path
from typing import Any

import numpy as np

from psf_parser._check import check
from psf_parser.errors import PsfParseError, PsfStructureError
from psf_parser.model import Kind, PsfFile, Role, Variable

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


def file_stamp(path: Path) -> tuple[int, int] | None:
    """The file's size and modification time, or None if it is gone."""
    try:
        status = os.stat(path)
    except OSError:
        return None
    return status.st_size, status.st_mtime_ns


def _check_unchanged(path: Path, stamp: tuple[int, int] | None) -> None:
    if file_stamp(path) != stamp:
        raise PsfParseError(f"{path} changed after it was loaded")


def defer_columns(
    file: PsfFile, path: Path, stamp: tuple[int, int] | None, read_columns: Callable[[], Mapping[str, Any]]
) -> None:
    """Arrange for the sweep and trace columns to be read when one of them is first asked for."""
    columns = [variable for variable in file if variable.role is not Role.ENTRY]

    def load() -> None:
        _check_unchanged(path, stamp)
        read = read_columns()
        for variable in columns:
            variable._values = as_column(variable.type.kind, read.get(variable.name, []))
        try:
            check(file)
        except PsfStructureError:
            for variable in columns:
                variable._values = None
            raise

    for variable in columns:
        variable._source = load


def defer_each_column(
    file: PsfFile, path: Path, stamp: tuple[int, int] | None, read_column: Callable[[Variable], Any]
) -> None:
    """Arrange for each sweep and trace column to be read on its own when it is first asked for."""

    def load(variable: Variable) -> None:
        _check_unchanged(path, stamp)
        variable._values = as_column(variable.type.kind, read_column(variable))

    for variable in file:
        if variable.role is not Role.ENTRY:
            variable._source = partial(load, variable)
