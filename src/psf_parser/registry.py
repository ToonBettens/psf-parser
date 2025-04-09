from __future__ import annotations
from typing import Optional, Union
from dataclasses import dataclass, field
from enum import Enum

dataclass_kw = dataclass(kw_only=True)

class Datatype(Enum):
    NONE = (0, None)
    STRING = (2, 'KW_STRING')
    ARRAY = (3, 'KW_ARRAY')
    INT = (5, 'KW_INT')
    FLOAT = (11, 'KW_FLOAT')
    COMPLEX = (12, 'KW_COMPLEX')
    STRUCT = (16, 'KW_STRUCT')

    def __init__(self, chunk_id, keyword):
        self._chunk_id = chunk_id
        self._keyword = keyword

    @property
    def chunk_id(self):
        return self._chunk_id

    @property
    def keyword(self):
        return self._keyword

    @classmethod
    def from_chunk_id(cls, chunk_id: int) -> 'Datatype':
        for member in cls:
            if member.chunk_id == chunk_id:
                return member
        raise ValueError(f"No Datatype with chunk_id {chunk_id}")

    @classmethod
    def from_keyword(cls, keyword: str) -> 'Datatype':
        for member in cls:
            if member.keyword == keyword:
                return member
        raise ValueError(f"No Datatype with keyword {keyword!r}")


@dataclass_kw
class Declaration:
    id: int
    name: str
    props: dict[str, str | int | float] = field(default_factory=dict)
    _registry: Optional[Registry] = None # set after adding to registry (back-reference)

@dataclass_kw
class TypeDeclaration(Declaration):
    datatype: Datatype

@dataclass_kw
class ArrayTypeDeclaration(TypeDeclaration):
    arraytype: Datatype

@dataclass_kw
class StructTypeDeclaration(TypeDeclaration):
    members: list = field(default_factory=list)

@dataclass_kw
class NonTypeDeclaration(Declaration):
    type_id: int

    def get_type(self) -> Optional[TypeDeclaration]:
        if self._registry:
            return self._registry.get_by_id(self.type_id)
        return None

@dataclass_kw
class SweepDeclaration(NonTypeDeclaration):
    data: list = field(default_factory=list)

@dataclass_kw
class TraceDeclaration(NonTypeDeclaration):
    data: list = field(default_factory=list)

@dataclass_kw
class ValueDeclaration(NonTypeDeclaration):
    data: str | int | float | list | dict = None


class Registry:

    def __init__(self):
        self._members_by_id: dict[int, Declaration] = {}
        self._members_by_name: dict[str, Declaration] = {}

    def add(self, member: Declaration):
        if member.id in self._members_by_id:
            raise ValueError(f"Duplicate id: {member.id}")
        if member.name in self._members_by_name:
            raise ValueError(f"Duplicate name: {member.name}")
        member._registry = self
        self._members_by_id[member.id] = member
        self._members_by_name[member.name] = member

    def get_all(self):
        return list(self._members_by_id.values())

    def get_by_id(self, id: int) -> Optional[Declaration]:
        return self._members_by_id.get(id)

    def get_by_name(self, name: str) -> Optional[Declaration]:
        return self._members_by_name.get(name)

    def generate_unique_id(self) -> int:
        if not self._members_by_id:
            return 1
        return max(self._members_by_id.keys()) + 1

    def __len__(self):
        return len(self._members_by_id)

    def __iter__(self):
        return iter(self._members_by_id.values())

    def __getitem__(self, key: Union[int, str]):
        if isinstance(key, int):
            return self._members_by_id[key]
        elif isinstance(key, str):
            return self._members_by_name[key]
        raise KeyError(f"Invalid key type: {key!r}")

    def __contains__(self, key: Union[int, str]):
        if isinstance(key, int):
            return key in self._members_by_id
        elif isinstance(key, str):
            return key in self._members_by_name
        raise KeyError(f"Invalid key type: {key!r}")

    def __repr__(self):
        return f"<Registry: {len(self)} members>"
