from __future__ import annotations

import re
from collections.abc import Collection, Iterator
from dataclasses import dataclass

from psf_parser.errors import PsfParseError

TOKEN_SPECIFICATION = [
    ("STRING", r'"(?:\\.|[^"\\])*"'),
    ("FLOAT", r"[+-]?(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?|[+-]?\d+[eE][+-]?\d+|[+-]?(?:inf|nan)"),
    ("INT", r"[+-]?[0-9]+"),
    ("KW", r"[A-Z]+"),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("SKIP", r"[\s*]+"),
    ("MISMATCH", r"."),
]

TOKEN_REGEX = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPECIFICATION))


@dataclass(frozen=True, slots=True)
class Token:
    kind: str
    value: str | int | float
    row: int
    column: int

    def matches(self, kinds: str | Collection[str]) -> bool:
        """True if this token is one of `kinds`."""
        return self.kind in ({kinds} if isinstance(kinds, str) else set(kinds))

    def __repr__(self) -> str:
        return f"{self.kind}({self.value!r}) at {self.row}:{self.column}"


class Tokenizer:
    """A stream of tokens over psfascii text, scanned as they are asked for."""

    def __init__(self, text: str, first_row: int = 1):
        self.tokens = self._scan(text, first_row)
        self.upcoming = next(self.tokens, None)

    def _scan(self, text: str, first_row: int) -> Iterator[Token]:
        row, column = first_row, 1
        for match in TOKEN_REGEX.finditer(text):
            kind = match.lastgroup
            assert kind is not None, "every alternative in TOKEN_REGEX is a named group"
            value = match.group(kind)
            length = len(value)

            match kind:
                case "SKIP":
                    for char in value:
                        row, column = (row + 1, 1) if char == "\n" else (row, column + 1)
                    continue
                case "MISMATCH":
                    raise PsfParseError(f"unexpected character {value!r} at line {row}, column {column}")
                case "STRING":
                    value = value[1:-1]
                case "FLOAT":
                    value = float(value)
                case "INT":
                    value = int(value)
                case "KW":
                    kind = "KW_" + value

            yield Token(kind, value, row, column)
            column += length

    def peek(self) -> Token | None:
        """The next token without consuming it."""
        return self.upcoming

    def at(self, kinds: str | Collection[str]) -> bool:
        """True if the next token is one of `kinds`, without consuming it."""
        token = self.peek()
        return token is not None and token.matches(kinds)

    def next(self) -> Token:
        """Consume and return the next token."""
        token = self.peek()
        if token is None:
            raise PsfParseError("unexpected end of file")
        self.upcoming = next(self.tokens, None)
        return token

    def expect(self, kinds: str | Collection[str]) -> Token:
        """Consume the next token, which must be one of `kinds`."""
        token = self.next()
        if not token.matches(kinds):
            raise PsfParseError(f"expected {kinds}, got {token.kind} at line {token.row}, column {token.column}")
        return token
