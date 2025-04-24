from __future__ import annotations
from abc import ABC
from enum import Enum
from collections.abc import Sequence, Mapping
from typing import Optional, Union

DeclarationId = int
Scalar = Union[int, float, complex, str]
Data = Union[
    Scalar,
    Sequence[Scalar],
    Mapping[str, Scalar],
]


class Section(Enum):
    HEADER = 'header'
    TYPE = 'type'
    SWEEP = 'sweep'
    TRACE = 'trace'
    VALUE = 'value'


class Datatype(Enum):
    NONE = 0
    INT8 = 1
    STRING = 2
    ARRAY = 3
    INT32 = 5
    FLOAT64 = 11
    COMPLEX = 12
    STRUCT = 16


class Declaration(ABC):
    def __init__(
        self,
        id: DeclarationId,
        name: str,
        section: Section,
        props: Optional[Mapping[str, Scalar]] = None
    ):
        self.id = id
        self.name = name
        self.section = section
        self.props = props if props is not None else {}

    def __repr__(self):
        return f"<{self.__class__.__name__}: id={self.id}, name={self.name}>"


class GroupDeclaration(Declaration):
    def __init__(
        self,
        id: DeclarationId,
        name: str,
        section: Section,
        members: Optional[list[DeclarationId]] = None,
        props: Optional[Mapping[str, Scalar]] = None
    ):
        super().__init__(id, name, section, props=props)
        self.members = members if members is not None else []


class TypeDeclaration(Declaration):
    def __init__(
        self,
        id: DeclarationId,
        name: str,
        section: Section,
        datatype: Datatype,
        props: Optional[Mapping[str, Scalar]] = None
    ):
        super().__init__(id, name, section, props=props)
        self.datatype = datatype


class ArrayTypeDeclaration(TypeDeclaration):
    def __init__(
        self,
        id: DeclarationId,
        name: str,
        section: Section,
        datatype: Datatype,
        arraytype: Datatype,
        props: Optional[Mapping[str, Scalar]] = None
    ):
        super().__init__(id, name, section, datatype, props=props)
        self.arraytype = arraytype


class StructTypeDeclaration(TypeDeclaration):
    def __init__(
        self,
        id: DeclarationId,
        name: str,
        section: Section,
        datatype: Datatype,
        members: Optional[list[DeclarationId]] = None,
        props: Optional[Mapping[str, Scalar]] = None
    ):
        super().__init__(id, name, section, datatype, props=props)
        self.members = members if members is not None else []


class DataDeclaration(Declaration):
    def __init__(
        self,
        id: DeclarationId,
        name: str,
        section: Section,
        type_id: DeclarationId,
        data: Optional[Data] = None,
        props: Optional[Mapping[str, Scalar]] = None
    ):
        if section not in { Section.SWEEP, Section.TRACE, Section.VALUE }:
            raise ValueError(f"Invalid section '{section}' for DataDeclaration.")
        super().__init__(id, name, section, props=props)
        self.type_id = type_id
        self.data = data
