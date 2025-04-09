import os
import time

from psf_parser.parser import PsfParser
from psf_parser.registry import Datatype, TypeDeclaration, SweepDeclaration, TraceDeclaration, ValueDeclaration
from psf_parser.binary.reader import BinaryReader
import psf_parser.binary.chunk_id as cid


class PsfBinParser(PsfParser):

    def __init__(self, path: str):
        super().__init__(path)
        self.timing = {}


    def parse(self):
        with open(self.path, 'rb') as f:
            self.reader = BinaryReader(f)

            self._parse_magic_number()
            self._parse_toc()
            self._validate_toc()

            for name, start in self.toc.items():
                start_timing = time.time()
                match name:
                    case 'HEADER':
                        self._parse_header_section(start)
                    case 'TYPE':
                        self._parse_type_section(start)
                    case 'SWEEP':
                        self._parse_sweep_section(start)
                    case 'TRACE':
                        self._parse_trace_section(start)
                    case 'VALUE':
                        self._parse_value_section(start)
                    case 'END':
                        continue
                self.timing[name] = time.time() - start_timing
            return self


    def _parse_magic_number(self):
        self.reader.goto(-12, os.SEEK_END)
        magic_number = self.reader.read_bytes(8).decode()
        if magic_number != 'Clarissa':
            raise SyntaxError("Footer magic number incorrect")


    def _parse_toc(self):
        translation_table = {
            cid.SECTION_HEADER: 'HEADER',
            cid.SECTION_TYPE: 'TYPE',
            cid.SECTION_SWEEP: 'SWEEP',
            cid.SECTION_TRACE: 'TRACE',
            cid.SECTION_VALUE: 'VALUE',
        }
        self.reader.goto(-4, os.SEEK_END)
        toc_offset = self.reader.read_int()
        toc_size = int((self.reader.filesize - toc_offset - 12)/8)

        self.reader.goto(toc_offset)
        for _ in range(toc_size):
            chunk_id = cid.validate(self.reader.read_int(), cid.section)
            offset = self.reader.read_int()
            section = translation_table.get(chunk_id)
            self.toc[section] = offset
        self.toc['END'] = toc_offset


    def _parse_header_section(self, start):
        self.reader.goto(start)
        cid.validate(self.reader.read_int(), cid.CONTAINER)
        endpos = self.reader.read_int() - 4
        while self.reader.pos < endpos:
            chunk_id = cid.validate(self.reader.read_int(), cid.property)
            key = self.reader.read_string()
            match chunk_id:
                case cid.PROP_STRING:
                    value = self.reader.read_string()
                case cid.PROP_INT:
                    value = self.reader.read_int()
                case cid.PROP_FLOAT:
                    value = self.reader.read_float()
            self.meta[key] = value


    def _parse_type_section(self, start):
        self.reader.goto(start)
        cid.validate(self.reader.read_int(), cid.CONTAINER)
        endpos = self.reader.read_int() - 4
        cid.validate(self.reader.read_int(), cid.CONTAINER_DATA)
        data_endpos = self.reader.read_int()
        while self.reader.pos < data_endpos:
            chunk_id = cid.validate(self.reader.read_int(), {cid.DECLARATION} | cid.property)
            match chunk_id:
                case cid.DECLARATION:
                    id = self.reader.read_int()
                    name = self.reader.read_string()
                    arraytype = Datatype.from_chunk_id(self.reader.read_int())
                    datatype = Datatype.from_chunk_id(self.reader.read_int())
                    match datatype:
                        case dt if dt in { Datatype.STRING, Datatype.INT, Datatype.FLOAT, Datatype.COMPLEX }:
                            decl = TypeDeclaration(
                                id = id,
                                name = name,
                                datatype = datatype
                            )
                            self.registry.add(decl)
                        case Datatype.ARRAY:
                            raise NotImplementedError()
                        case Datatype.STRUCT:
                            raise NotImplementedError()
                case cid.PROP_STRING:
                    key = self.reader.read_string()
                    value = self.reader.read_string()
                    decl.props[key] = value
                case cid.PROP_INT:
                    key = self.reader.read_string()
                    value = self.reader.read_int()
                    decl.props[key] = value
                case cid.PROP_FLOAT:
                    key = self.reader.read_string()
                    value = self.reader.read_float()
                    decl.props[key] = value


    def _parse_sweep_section(self, start):
        self.reader.goto(start)
        cid.validate(self.reader.read_int(), cid.CONTAINER)
        endpos = self.reader.read_int() - 4
        while self.reader.pos < endpos:
            chunk_id = cid.validate(self.reader.read_int(), {cid.DECLARATION} | cid.property)
            match chunk_id:
                case cid.DECLARATION:
                    id = self.reader.read_int()
                    name = self.reader.read_string()
                    type_id = self.reader.read_int()
                    decl = SweepDeclaration(id=id, name=name, type_id=type_id)
                    self.registry.add(decl)
                case cid.PROP_STRING:
                    key = self.reader.read_string()
                    value = self.reader.read_string()
                    decl.props[key] = value
                case cid.PROP_INT:
                    key = self.reader.read_string()
                    value = self.reader.read_int()
                    decl.props[key] = value
                case cid.PROP_FLOAT:
                    key = self.reader.read_string()
                    value = self.reader.read_float()
                    decl.props[key] = value


    def _parse_trace_section(self, start):
        self.reader.goto(start)
        cid.validate(self.reader.read_int(), cid.CONTAINER)
        endpos = self.reader.read_int() - 4
        cid.validate(self.reader.read_int(), cid.CONTAINER_DATA)
        data_endpos = self.reader.read_int()
        while self.reader.pos < data_endpos:
            chunk_id = cid.validate(self.reader.read_int(), {cid.DECLARATION} | cid.section)
            match chunk_id:
                case cid.DECLARATION:
                    id = self.reader.read_int()
                    name = self.reader.read_string()
                    type_id = self.reader.read_int()
                    decl = TraceDeclaration(id=id, name=name, type_id=type_id)
                    self.registry.add(decl)
                case cid.PROP_STRING:
                    key = self.reader.read_string()
                    value = self.reader.read_string()
                    decl.props[key] = value
                case cid.PROP_INT:
                    key = self.reader.read_string()
                    value = self.reader.read_int()
                    decl.props[key] = value
                case cid.PROP_FLOAT:
                    key = self.reader.read_string()
                    value = self.reader.read_float()
                    decl.props[key] = value


    def _parse_value_section(self, start):
        self.reader.goto(start)
        cid.validate(self.reader.read_int(), cid.CONTAINER)
        endpos = self.reader.read_int() - 4

        if 'SWEEP' in self.toc.keys() and 'TRACE' in self.toc.keys():
            while self.reader.pos < endpos:
                cid.validate(self.reader.read_int(), cid.DECLARATION)
                decl = self.registry.get_by_id(self.reader.read_int())
                type_decl = decl.get_type()
                decl.data.append(self._parse_value_for_type(type_decl))

        else:
            cid.validate(self.reader.read_int(), cid.CONTAINER_DATA)
            data_endpos = self.reader.read_int() - 4
            while self.reader.pos < data_endpos:
                chunk_id = cid.validate(self.reader.read_int(), {cid.DECLARATION} | cid.section)
                match chunk_id:
                    case cid.DECLARATION:
                        id = self.reader.read_int()
                        name = self.reader.read_string()
                        type_id = self.reader.read_int()
                        data = self._parse_value_for_type(self.registry.get_by_id(type_id))
                        decl = ValueDeclaration(id=id, name=name, type_id=type_id, data=data)
                        self.registry.add(decl)
                    case cid.PROP_STRING:
                        key = self.reader.read_string()
                        value = self.reader.read_string()
                        decl.props[key] = value
                    case cid.PROP_INT:
                        key = self.reader.read_string()
                        value = self.reader.read_int()
                        decl.props[key] = value
                    case cid.PROP_FLOAT:
                        key = self.reader.read_string()
                        value = self.reader.read_float()
                        decl.props[key] = value


    def _parse_value_for_type(self, type_decl):
        match type_decl.datatype:
            case dt if dt in {Datatype.STRING, Datatype.INT, Datatype.FLOAT, Datatype.COMPLEX}:
                return self._parse_value_for_datatype(type_decl.datatype)
            case Datatype.ARRAY:
                raise NotImplementedError()
            case Datatype.STRUCT:
                raise NotImplementedError()

    def _parse_value_for_datatype(self, datatype):
        match datatype:
            case Datatype.STRING:
                return self.reader.read_string()
            case Datatype.INT:
                return self.reader.read_int()
            case Datatype.FLOAT:
                return self.reader.read_float()
            case Datatype.COMPLEX:
                return complex(self.reader.read_float(), self.reader.read_float())
            case _:
                raise SyntaxError(f'Unexpected basic datatype {datatype}')
