from __future__ import annotations

from collections.abc import Collection
from enum import Enum

from psf_parser.errors import PsfParseError


class ChunkId(Enum):
    """The tag that opens every chunk of a psfbin file."""

    SECTION_HEADER = 0
    SECTION_TYPE = 1
    SECTION_SWEEP = 2
    SECTION_TRACE = 3
    SECTION_VALUE = 4
    SECTION_END = 15

    DECLARATION = 16
    GROUP_DECLARATION = 17
    STRUCT_END = 18

    CONTAINER_INDEX = 19
    CONTAINER_PADDING = 20
    CONTAINER = 21
    SUBCONTAINER = 22

    PROP_STRING = 33
    PROP_INT = 34
    PROP_FLOAT = 35

    @classmethod
    def _missing_(cls, value: object) -> None:
        raise PsfParseError(f"unknown chunk id {value}")

    @classmethod
    def properties(cls) -> set[ChunkId]:
        """The ids that open a property, of the three types psfbin can store."""
        return {cls.PROP_STRING, cls.PROP_INT, cls.PROP_FLOAT}

    def matches(self, ids: ChunkId | Collection[ChunkId]) -> bool:
        """True if this id is one of `ids`."""
        return self in ({ids} if isinstance(ids, ChunkId) else set(ids))
