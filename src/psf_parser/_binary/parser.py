from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from psf_parser._binary.chunk import ChunkId
from psf_parser._binary.reader import BinaryReader
from psf_parser.builder import PsfBuilder
from psf_parser.errors import PsfParseError
from psf_parser.model import Kind, PsfFile, PsfType, Role, Scalar

KINDS = {
    1: Kind.INT8,
    2: Kind.STRING,
    3: Kind.ARRAY,
    5: Kind.INT32,
    11: Kind.FLOAT64,
    12: Kind.COMPLEX,
    16: Kind.STRUCT,
}

MAGIC = b"Clarissa"


class ValueSection(Enum):
    """How the VALUE section is laid out, declared by the file's first word."""

    NONE = 0
    TAGGED = 512
    WINDOWED = 1024
    ENTRIES = 1280


class BinaryParser:
    """Parses one psfbin file into a `PsfFile`."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.builder = PsfBuilder(str(self.path))
        self.types_by_id: dict[int, PsfType] = {}
        self.names_by_id: dict[int, str] = {}

    def parse(self) -> PsfFile:
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
            self.reader.close()

        return self.builder.build()

    def _validate_signature(self) -> None:
        try:
            self.reader.seek(-12, 2)
        except OSError:
            raise PsfParseError(f"{self.path} is too short to be a psfbin file") from None
        if self.reader.read_bytes(8) != MAGIC:
            raise PsfParseError(f"{self.path} is not a psfbin file (magic missing)")

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
                    properties[key] = self.reader.read_uint32()
                case ChunkId.PROP_FLOAT:
                    properties[key] = self.reader.read_float64()

    def _read_type(self) -> PsfType:
        self._expect(ChunkId.DECLARATION)
        type_id = self.reader.read_uint32()
        name = self.reader.read_string()
        element_code = self.reader.read_uint32()
        kind = KINDS[self.reader.read_uint32()]

        element = PsfType(name, KINDS[element_code]) if kind is Kind.ARRAY else None
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
        type_ = self.types_by_id[self.reader.read_uint32()]
        self.names_by_id[variable_id] = name
        self.builder.declare(name, type_, role, self._read_properties())

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
                return self.reader.read_uint32()
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
        for key, value in self._read_properties().items():
            self.builder.add_header(key, value)
        self._close_container(end)

    def _parse_types(self) -> None:
        end = self._open_container(ChunkId.CONTAINER)
        inner = self._open_container(ChunkId.SUBCONTAINER)
        while self.reader.tell() < inner:
            self.builder.add_type(self._read_type())
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
        end = self._open_container(ChunkId.CONTAINER)
        match self.value_section:
            case ValueSection.NONE:
                pass
            case ValueSection.ENTRIES:
                self._parse_entry_values()
            case ValueSection.TAGGED:
                self._parse_tagged_values(end)
            case ValueSection.WINDOWED:
                self._parse_windowed_values(end)
        self._close_container(end)
        self._expect(ChunkId.SECTION_END)

    # --- values -------------------------------------------------------------

    def _parse_entry_values(self) -> None:
        inner = self._open_container(ChunkId.SUBCONTAINER)
        while self.reader.tell() < inner:
            self._expect(ChunkId.DECLARATION)
            self.reader.skip(4)
            name = self.reader.read_string()
            type_ = self.types_by_id[self.reader.read_uint32()]
            self.builder.add_value(name, type_, self._read_value(type_), self._read_properties())
        self._skip_index(bytes_per_entry=8)

    def _parse_tagged_values(self, end: int) -> None:
        while self.reader.tell() < end:
            self._expect(ChunkId.DECLARATION)
            name = self.names_by_id[self.reader.read_uint32()]
            variable = self.builder.variable_named(name)
            self.builder.append(name, self._read_value(variable.type))

    def _parse_windowed_values(self, end: int) -> None:
        sweeps = [s for s in self.builder.variables.values() if s.role is Role.SWEEP]
        if len(sweeps) != 1:
            raise PsfParseError(f"windowed layout needs exactly one sweep, found {len(sweeps)}")
        columns = sweeps + [s for s in self.builder.variables.values() if s.role is Role.TRACE]

        while True:
            self._skip_padding(end)
            if self.reader.tell() >= end:
                return

            self._expect(ChunkId.DECLARATION)
            window = self.reader.read_uint16()
            count = self.reader.read_uint16()

            for index, variable in enumerate(columns):
                self.builder.extend(variable.name, [self.reader.read_float64() for _ in range(count)])
                self.reader.skip((window - count) * 8)
                if index < len(columns) - 1:
                    self.reader.skip(8)
