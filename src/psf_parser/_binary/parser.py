from __future__ import annotations

from collections import defaultdict
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

from psf_parser._binary.chunk import ChunkId
from psf_parser._binary.reader import BinaryReader
from psf_parser._check import add_type, add_variable
from psf_parser._columns import as_column, defer_columns, defer_each_column, file_stamp
from psf_parser.errors import PsfParseError
from psf_parser.model import Kind, PsfFile, PsfType, Role, Scalar, Variable

KINDS = {
    1: Kind.INT8,
    2: Kind.STRING,
    3: Kind.ARRAY,
    5: Kind.INT32,
    11: Kind.FLOAT64,
    12: Kind.COMPLEX,
    14: Kind.STRING,  # Declared with one extra word (format-notes 3.4).
    16: Kind.STRUCT,
}

STRING_WITH_EXTRA_WORD = 14
MAGIC = b"Clarissa"
# Spectre 25.1 pads up to 45 KB after the magic (format-notes 3.1), so 1 MiB leaves a wide margin.
SIGNATURE_SEARCH_LIMIT = 1 << 20

# Big-endian dtypes of the kinds a tagged row can hold at a fixed size (format-notes 3.5).
FIXED_SIZE_DTYPES = {Kind.FLOAT64: ">f8", Kind.COMPLEX: ">c16"}


class ValueSection(Enum):
    """How the VALUE section is laid out, declared by the file's first word."""

    NONE = 0
    TAGGED = 512
    WINDOWED = 1024
    ENTRIES = 1280

    @classmethod
    def _missing_(cls, value: object) -> None:
        raise PsfParseError(f"unknown value section layout {value}")


class BinaryParser:
    """Parses one psfbin file: its declarations at once, and the columns of a table when asked."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.file = PsfFile(path=self.path)
        self.types_by_id: dict[int, PsfType] = {}
        self.variables_by_id: dict[int, Variable] = {}
        self.values_at = 0
        self.stamp = None
        self.windowed: list[Variable] = []
        self.blocks: list[tuple[int, int, int]] | None = None

    def read_schema(self) -> PsfFile:
        self.stamp = file_stamp(self.path)
        with open(self.path, "rb") as handle:
            self.reader = BinaryReader(handle)
            self._validate_signature()
            self.reader.seek(0)

            self.value_section = ValueSection(self.reader.read_uint32())
            self._parse_header()
            self._parse_if(ChunkId.SECTION_TYPE, self._parse_types)
            self._parse_if(ChunkId.SECTION_SWEEP, self._parse_sweeps)
            self._parse_if(ChunkId.SECTION_TRACE, self._parse_traces)
            self._parse_if(ChunkId.SECTION_VALUE, self._parse_values)
        return self.file

    def read_columns(self) -> dict[str, Any]:
        """Every column of a tagged file."""
        with open(self.path, "rb") as handle:
            self.reader = BinaryReader(handle)
            self.reader.seek(self.values_at)
            end = self._open_container(ChunkId.CONTAINER)
            columns = self._read_tagged_values(end)
            self._close_container(end)
            self._expect(ChunkId.SECTION_END)
        return columns

    def read_column(self, variable: Variable) -> np.ndarray | list[float]:
        """One column of a windowed file, from each block in turn."""
        index = self.windowed.index(variable)
        with open(self.path, "rb") as handle:
            self.reader = BinaryReader(handle)
            parts = []
            for start, window, count in self._window_blocks():
                self.reader.seek(start + index * (window + 1) * 8)
                parts.append(np.frombuffer(self.reader.read_bytes(count * 8), dtype=">f8"))
        return np.concatenate(parts) if parts else []

    def _validate_signature(self) -> None:
        """Find the magic near the end, where padding can follow it (format-notes 3.1)."""
        self.reader.seek(0, 2)
        self.reader.seek(max(self.reader.tell() - SIGNATURE_SEARCH_LIMIT, 0))
        if MAGIC in self.reader.fp.read():
            return
        raise PsfParseError(f"{self.path} is not a psfascii or psfbin file, or is truncated (psfxl is not supported)")

    def _at(self, ids: ChunkId | set[ChunkId]) -> bool:
        """True if the next chunk id is one of `ids`, without consuming it."""
        return ChunkId(self.reader.peek_uint32()).matches(ids)

    def _expect(self, ids: ChunkId | set[ChunkId]) -> ChunkId:
        """Consume the next chunk id, which must be one of `ids`."""
        offset = self.reader.tell()
        chunk = ChunkId(self.reader.read_uint32())
        if not chunk.matches(ids):
            raise PsfParseError(f"expected {ids}, got {chunk} at offset {offset}")
        return chunk

    def _parse_if(self, section: ChunkId, parse) -> None:
        if self._at(section):
            self.reader.skip(4)
            parse()

    # --- containers ---------------------------------------------------------

    def _open_container(self, chunk: ChunkId) -> int:
        self._expect(chunk)
        size = self.reader.read_uint32()
        return size - 4 if chunk is ChunkId.CONTAINER else size

    def _close_container(self, end: int) -> None:
        if self.reader.tell() != end:
            raise PsfParseError(f"container ended at {self.reader.tell()}, expected {end}")

    def _skip_index(self, bytes_per_entry: int) -> None:
        """Skip a CONTAINER_INDEX, checking its size is a whole number of entries."""
        self._expect(ChunkId.CONTAINER_INDEX)
        size = self.reader.read_uint32()
        if size % bytes_per_entry != 0:
            raise PsfParseError(f"index size {size} is not a multiple of {bytes_per_entry} bytes per entry")
        self.reader.skip(size)

    def _skip_padding(self, end: int) -> None:
        while self.reader.tell() < end and self._at(ChunkId.CONTAINER_PADDING):
            self.reader.skip(4)
            self.reader.skip(self.reader.read_uint32())

    # --- declarations -------------------------------------------------------

    def _read_properties(self) -> dict[str, Scalar]:
        properties = {}
        while True:
            chunk = ChunkId(self.reader.peek_uint32())
            if not chunk.matches(ChunkId.properties()):
                return properties
            self.reader.skip(4)
            key = self.reader.read_string()
            match chunk:
                case ChunkId.PROP_STRING:
                    properties[key] = self.reader.read_string()
                case ChunkId.PROP_INT:
                    properties[key] = self.reader.read_int32()
                case ChunkId.PROP_FLOAT:
                    properties[key] = self.reader.read_float64()

    def _kind(self, code: int) -> Kind:
        if code not in KINDS:
            raise PsfParseError(f"unknown type code {code} before offset {self.reader.tell()}")
        return KINDS[code]

    def _type_by_id(self) -> PsfType:
        type_id = self.reader.read_uint32()
        if type_id not in self.types_by_id:
            raise PsfParseError(f"unknown type id {type_id} before offset {self.reader.tell()}")
        return self.types_by_id[type_id]

    def _read_type(self) -> PsfType:
        self._expect(ChunkId.DECLARATION)
        type_id = self.reader.read_uint32()
        name = self.reader.read_string()
        element_code = self.reader.read_uint32()
        code = self.reader.read_uint32()
        kind = self._kind(code)
        if code == STRING_WITH_EXTRA_WORD:
            self.reader.skip(4)

        element = PsfType(name, self._kind(element_code)) if kind is Kind.ARRAY else None
        fields: tuple[PsfType, ...] = ()
        if kind is Kind.STRUCT:
            members = []
            while not self._at(ChunkId.STRUCT_END):
                members.append(self._read_type())
            self.reader.skip(4)
            fields = tuple(members)

        type_ = PsfType(name, kind, self._read_properties(), element=element, fields=fields)
        self.types_by_id[type_id] = type_
        return type_

    def _read_variable(self, role: Role) -> None:
        chunk = self._expect({ChunkId.DECLARATION, ChunkId.GROUP_DECLARATION})
        if chunk is ChunkId.GROUP_DECLARATION:
            self._read_group(role)
            return

        variable_id = self.reader.read_uint32()
        name = self.reader.read_string()
        type_ = self._type_by_id()
        self.variables_by_id[variable_id] = add_variable(
            self.file, Variable(name, type_, role, self._read_properties())
        )

    def _read_group(self, role: Role) -> None:
        self.reader.skip(4)  # group id
        self.reader.read_string()  # group name, always "group" (so far)
        for _ in range(self.reader.read_uint32()):
            self._read_variable(role)

    def _read_value(self, type_: PsfType) -> Any:
        match type_.kind:
            case Kind.INT8:
                # A signed byte in a four-byte big-endian slot: the value is last.
                self.reader.skip(3)
                return self.reader.read_int8()
            case Kind.INT32:
                return self.reader.read_int32()
            case Kind.FLOAT64:
                return self.reader.read_float64()
            case Kind.COMPLEX:
                return complex(self.reader.read_float64(), self.reader.read_float64())
            case Kind.STRING:
                return self.reader.read_string()
            case Kind.STRUCT:
                return {f.name: self._read_value(f) for f in type_.fields}
            case Kind.ARRAY:
                raise NotImplementedError("array values are not supported in psfbin yet")

    # --- sections -----------------------------------------------------------

    def _parse_header(self) -> None:
        end = self._open_container(ChunkId.CONTAINER)
        self.file.header.update(self._read_properties())
        self._close_container(end)

    def _parse_types(self) -> None:
        end = self._open_container(ChunkId.CONTAINER)
        inner = self._open_container(ChunkId.SUBCONTAINER)
        while self.reader.tell() < inner:
            add_type(self.file, self._read_type())
        self._skip_index(bytes_per_entry=8)
        self._close_container(end)

    def _parse_sweeps(self) -> None:
        end = self._open_container(ChunkId.CONTAINER)
        while self.reader.tell() < end:
            self._read_variable(Role.SWEEP)
        self._close_container(end)

    def _parse_traces(self) -> None:
        end = self._open_container(ChunkId.CONTAINER)
        inner = self._open_container(ChunkId.SUBCONTAINER)
        while self.reader.tell() < inner:
            self._read_variable(Role.TRACE)
        self._skip_index(bytes_per_entry=16)
        self._close_container(end)

    def _parse_values(self) -> None:
        if self.value_section is ValueSection.TAGGED:
            self.values_at = self.reader.tell()
            defer_columns(self.file, self.path, self.stamp, self.read_columns)
            return
        if self.value_section is ValueSection.WINDOWED:
            self.values_at = self.reader.tell()
            self.windowed = self._windowed_columns()
            defer_each_column(self.file, self.path, self.stamp, self.read_column)
            return
        end = self._open_container(ChunkId.CONTAINER)
        if self.value_section is ValueSection.ENTRIES:
            self._parse_entry_values()
        self._close_container(end)
        self._expect(ChunkId.SECTION_END)

    # --- values -------------------------------------------------------------

    def _parse_entry_values(self) -> None:
        inner = self._open_container(ChunkId.SUBCONTAINER)
        while self.reader.tell() < inner:
            self._expect(ChunkId.DECLARATION)
            self.reader.skip(4)
            name = self.reader.read_string()
            type_ = self._type_by_id()
            value = as_column(type_.kind, [self._read_value(type_)])
            add_variable(self.file, Variable(name, type_, Role.ENTRY, self._read_properties(), value))
        self._skip_index(bytes_per_entry=8)

    def _read_tagged_values(self, end: int) -> dict[str, Any]:
        start = self.reader.tell()
        columns = self._read_fixed_rows(end)
        if columns is None:
            self.reader.seek(start)
            columns = self._walk_tagged_values(end)
        return columns

    def _read_fixed_rows(self, end: int) -> dict[str, np.ndarray] | None:
        """Decode the rows as one array, or return None if they are not all the same shape."""
        start = self.reader.tell()
        names = []
        fields: list[tuple[str, str]] = []
        for index in range(len(self.variables_by_id)):
            if self.reader.tell() >= end or self.reader.read_uint32() != ChunkId.DECLARATION.value:
                return None
            variable = self.variables_by_id.get(self.reader.read_uint32())
            dtype = FIXED_SIZE_DTYPES.get(variable.type.kind) if variable else None
            if variable is None or dtype is None or variable.name in names:
                return None
            names.append(variable.name)
            fields += [(f"tag{index}", ">u4"), (f"id{index}", ">u4"), (f"value{index}", dtype)]
            self.reader.skip(np.dtype(dtype).itemsize)

        row = np.dtype(fields)
        size = end - start
        if not names or size % row.itemsize != 0:
            return None
        self.reader.seek(start)
        rows = np.frombuffer(self.reader.read_bytes(size), dtype=row)
        for index, column in enumerate(rows[0][f"id{i}"] for i in range(len(names))):
            if (rows[f"tag{index}"] != ChunkId.DECLARATION.value).any() or (rows[f"id{index}"] != column).any():
                return None
        return {name: rows[f"value{index}"] for index, name in enumerate(names)}

    def _walk_tagged_values(self, end: int) -> dict[str, list[Any]]:
        """Read the rows value by value, which works whatever their sizes and order."""
        columns: defaultdict[str, list[Any]] = defaultdict(list)
        while self.reader.tell() < end:
            self._expect(ChunkId.DECLARATION)
            variable_id = self.reader.read_uint32()
            if variable_id not in self.variables_by_id:
                raise PsfParseError(f"unknown column id {variable_id} before offset {self.reader.tell()}")
            variable = self.variables_by_id[variable_id]
            columns[variable.name].append(self._read_value(variable.type))
        return columns

    def _windowed_columns(self) -> list[Variable]:
        sweeps = [v for v in self.file if v.role is Role.SWEEP]
        if len(sweeps) != 1:
            raise PsfParseError(f"windowed layout needs exactly one sweep, found {len(sweeps)}")
        columns = sweeps + self.file.traces
        for variable in columns:
            if variable.type.kind is not Kind.FLOAT64:
                raise PsfParseError(f"windowed column {variable.name!r} is {variable.type.kind.value}, not float64")
        return columns

    def _window_blocks(self) -> list[tuple[int, int, int]]:
        """Where each block's data starts, with its window and count, scanned once (format-notes 3.6)."""
        if self.blocks is None:
            self.reader.seek(self.values_at)
            end = self._open_container(ChunkId.CONTAINER)
            blocks = []
            while True:
                self._skip_padding(end)
                if self.reader.tell() >= end:
                    break
                self._expect(ChunkId.DECLARATION)
                window = self.reader.read_uint16()
                count = self.reader.read_uint16()
                if count > window:
                    raise PsfParseError(
                        f"block before offset {self.reader.tell()} holds {count} values in {window} slots"
                    )
                blocks.append((self.reader.tell(), window, count))
                self.reader.skip((len(self.windowed) * (window + 1) - 1) * 8)
            self._close_container(end)
            self._expect(ChunkId.SECTION_END)
            self.blocks = blocks
        return self.blocks
