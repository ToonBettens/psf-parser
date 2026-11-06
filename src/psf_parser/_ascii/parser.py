from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any, BinaryIO

from psf_parser._ascii.tokenizer import Tokenizer
from psf_parser._check import add_type, add_variable
from psf_parser._columns import as_column, defer_columns, file_stamp
from psf_parser.errors import PsfParseError, PsfStructureError
from psf_parser.model import Kind, PsfFile, PsfType, Role, Scalar, Variable

SCALAR_KINDS = {
    "KW_STRING": Kind.STRING,
    ("KW_INT", "KW_BYTE"): Kind.INT8,
    ("KW_INT", "KW_LONG"): Kind.INT32,
    ("KW_FLOAT", "KW_DOUBLE"): Kind.FLOAT64,
    ("KW_COMPLEX", "KW_DOUBLE"): Kind.COMPLEX,
}

SECTIONS = {"KW_TYPE", "KW_SWEEP", "KW_TRACE", "KW_VALUE", "KW_END"}


class AsciiParser:
    """Parses one psfascii file: its declarations at once, and the columns of a table when asked."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.file = PsfFile(path=str(self.path))
        self.values_at = 0
        self.values_row = 1

    def read_schema(self) -> PsfFile:
        stamp = file_stamp(self.path)
        with open(self.path, "rb") as handle:
            self._check_complete(handle)
            handle.seek(0)
            self.tokenizer = Tokenizer(self._read_up_to_values(handle))
            self._parse_header()
            if self.tokenizer.at("KW_TYPE"):
                self._parse_section("KW_TYPE", self._read_type_declaration)
            if self.tokenizer.at("KW_SWEEP"):
                self._parse_section("KW_SWEEP", lambda: self._read_variable(Role.SWEEP))
            if self.tokenizer.at("KW_TRACE"):
                self._parse_section("KW_TRACE", lambda: self._read_variable(Role.TRACE))
            if self.tokenizer.at("KW_VALUE"):
                self.tokenizer.expect("KW_VALUE")
                if self.tokenizer.peek() is not None:
                    raise PsfParseError(f"{self.path}: VALUE is not on a line of its own")
                if self.file.sweep is None:
                    self.tokenizer = Tokenizer(handle.read().decode(), self.values_row)
                    self._parse_entries()
                else:
                    defer_columns(self.file, self.path, stamp, self.read_columns)
        return self.file

    def read_columns(self) -> dict[str, list[Any]]:
        with open(self.path, "rb") as handle:
            handle.seek(self.values_at)
            self.tokenizer = Tokenizer(handle.read().decode(), self.values_row)
        columns: defaultdict[str, list[Any]] = defaultdict(list)
        while not self.tokenizer.at("KW_END"):
            name = str(self.tokenizer.expect("STRING").value)
            columns[name].append(self._read_value(self._variable_named(name).type))
        return columns

    def _check_complete(self, handle: BinaryIO) -> None:
        handle.seek(0, 2)
        handle.seek(max(handle.tell() - 16, 0))
        if not handle.read().rstrip().endswith(b"END"):
            raise PsfParseError(f"{self.path} is truncated: it does not end in END")

    def _read_up_to_values(self, handle: BinaryIO) -> str:
        """The text up to and including the VALUE line, or all of it if there is no such line."""
        lines = []
        for line in handle:
            lines.append(line)
            self.values_at += len(line)
            self.values_row += 1
            if line.strip() == b"VALUE":
                break
        return b"".join(lines).decode()

    # --- sections -----------------------------------------------------------

    def _parse_header(self) -> None:
        self.tokenizer.expect("KW_HEADER")
        while not self.tokenizer.at(SECTIONS):
            key = str(self.tokenizer.expect("STRING").value)
            value = self.tokenizer.expect({"STRING", "INT", "FLOAT"}).value
            self.file.header[key] = value

    def _parse_section(self, keyword: str, read_one: Callable[[], Any]) -> None:
        self.tokenizer.expect(keyword)
        while not self.tokenizer.at(SECTIONS):
            read_one()

    def _parse_entries(self) -> None:
        while not self.tokenizer.at("KW_END"):
            name = str(self.tokenizer.expect("STRING").value)
            type_ = self._type_named(str(self.tokenizer.expect("STRING").value))
            value = as_column(type_.kind, [self._read_value(type_)])
            add_variable(self.file, Variable(name, type_, Role.ENTRY, self._read_properties(), value))

    # --- declarations -------------------------------------------------------

    def _read_type_declaration(self) -> None:
        add_type(self.file, self._read_type())

    def _type_named(self, name: str) -> PsfType:
        if name not in self.file.types:
            raise PsfStructureError(f"undeclared type {name!r} referenced by a declaration")
        return self.file.types[name]

    def _variable_named(self, name: str) -> Variable:
        if name not in self.file.variables:
            raise PsfStructureError(f"value for undeclared variable {name!r}")
        return self.file.variables[name]

    def _read_type(self) -> PsfType:
        name = str(self.tokenizer.expect("STRING").value)
        keyword = self.tokenizer.expect({"KW_STRING", "KW_INT", "KW_FLOAT", "KW_COMPLEX", "KW_ARRAY", "KW_STRUCT"})

        match keyword.kind:
            case "KW_ARRAY":
                self.tokenizer.expect("LPAREN")
                self.tokenizer.expect("RPAREN")
                element = self._read_scalar_kind()
                return PsfType(name, Kind.ARRAY, self._read_properties(), element=PsfType(name, element))

            case "KW_STRUCT":
                self.tokenizer.expect("LPAREN")
                fields = []
                while not self.tokenizer.at("RPAREN"):
                    fields.append(self._read_type())
                self.tokenizer.expect("RPAREN")
                return PsfType(name, Kind.STRUCT, self._read_properties(), fields=tuple(fields))

            case _:
                kind = self._resolve_scalar(keyword.kind)
                return PsfType(name, kind, self._read_properties())

    def _read_scalar_kind(self) -> Kind:
        keyword = self.tokenizer.expect({"KW_STRING", "KW_INT", "KW_FLOAT", "KW_COMPLEX"})
        return self._resolve_scalar(keyword.kind)

    def _resolve_scalar(self, keyword: str) -> Kind:
        if keyword == "KW_STRING":
            return Kind.STRING
        width = self.tokenizer.expect({"KW_DOUBLE", "KW_LONG", "KW_BYTE"}).kind
        try:
            return SCALAR_KINDS[(keyword, width)]
        except KeyError:
            raise PsfParseError(f"unknown scalar type {keyword} {width}") from None

    def _read_variable(self, role: Role) -> Variable:
        name = str(self.tokenizer.expect("STRING").value)
        type_ = self._type_named(str(self.tokenizer.expect("STRING").value))
        return add_variable(self.file, Variable(name, type_, role, self._read_properties()))

    # --- values -------------------------------------------------------------

    def _read_value(self, type_: PsfType) -> Any:
        match type_.kind:
            case Kind.ARRAY:
                assert type_.element is not None, "an ARRAY type always declares its element type"
                self.tokenizer.expect("LPAREN")
                values = []
                while not self.tokenizer.at("RPAREN"):
                    values.append(self._read_value(type_.element))
                self.tokenizer.expect("RPAREN")
                return values

            case Kind.STRUCT:
                self.tokenizer.expect("LPAREN")
                value = {f.name: self._read_value(f) for f in type_.fields}
                self.tokenizer.expect("RPAREN")
                return value

            case Kind.COMPLEX:
                self.tokenizer.expect("LPAREN")
                real = float(self.tokenizer.expect({"FLOAT", "INT"}).value)
                imaginary = float(self.tokenizer.expect({"FLOAT", "INT"}).value)
                self.tokenizer.expect("RPAREN")
                return complex(real, imaginary)

            case Kind.FLOAT64:
                return float(self.tokenizer.expect({"FLOAT", "INT"}).value)
            case Kind.STRING:
                return str(self.tokenizer.expect("STRING").value)
            case _:
                return self.tokenizer.expect("INT").value

    # --- shared -------------------------------------------------------------

    def _read_properties(self) -> dict[str, Scalar]:
        if not self.tokenizer.at("KW_PROP"):
            return {}
        self.tokenizer.expect("KW_PROP")
        self.tokenizer.expect("LPAREN")
        properties = {}
        while not self.tokenizer.at("RPAREN"):
            key = str(self.tokenizer.expect("STRING").value)
            properties[key] = self.tokenizer.expect({"STRING", "INT", "FLOAT"}).value
        self.tokenizer.expect("RPAREN")
        return properties
