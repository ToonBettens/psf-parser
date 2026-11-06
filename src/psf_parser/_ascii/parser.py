from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from psf_parser._ascii.tokenizer import Tokenizer
from psf_parser.builder import PsfBuilder
from psf_parser.errors import PsfParseError
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
    """Parses one psfascii file into a `PsfFile`."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.tokenizer = Tokenizer(self.path.read_text())
        self.builder = PsfBuilder(str(self.path))

    def parse(self) -> PsfFile:
        self._parse_header()
        if self.tokenizer.at("KW_TYPE"):
            self._parse_section("KW_TYPE", self._read_type_declaration)
        if self.tokenizer.at("KW_SWEEP"):
            self._parse_section("KW_SWEEP", lambda: self._read_variable(Role.SWEEP))
        if self.tokenizer.at("KW_TRACE"):
            self._parse_section("KW_TRACE", lambda: self._read_variable(Role.TRACE))
        if self.tokenizer.at("KW_VALUE"):
            self._parse_values()
        return self.builder.build()

    # --- sections -----------------------------------------------------------

    def _parse_header(self) -> None:
        self.tokenizer.expect("KW_HEADER")
        while not self.tokenizer.at(SECTIONS):
            key = str(self.tokenizer.expect("STRING").value)
            value = self.tokenizer.expect({"STRING", "INT", "FLOAT"}).value
            self.builder.add_header(key, value)

    def _parse_section(self, keyword: str, read_one: Callable[[], Any]) -> None:
        self.tokenizer.expect(keyword)
        while not self.tokenizer.at(SECTIONS):
            read_one()

    def _parse_values(self) -> None:
        self.tokenizer.expect("KW_VALUE")
        swept = any(s.role is Role.SWEEP for s in self.builder.variables.values())
        while not self.tokenizer.at("KW_END"):
            if swept:
                name = str(self.tokenizer.expect("STRING").value)
                variable = self.builder.variable_named(name)
                self.builder.append(name, self._read_value(variable.type))
            else:
                name = str(self.tokenizer.expect("STRING").value)
                type_ = self.builder.type_named(str(self.tokenizer.expect("STRING").value))
                self.builder.add_value(name, type_, self._read_value(type_), self._read_properties())

    # --- declarations -------------------------------------------------------

    def _read_type_declaration(self) -> PsfType:
        return self.builder.add_type(self._read_type())

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
        type_ = self.builder.type_named(str(self.tokenizer.expect("STRING").value))
        return self.builder.declare(name, type_, role, self._read_properties())

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
