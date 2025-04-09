import time
from pathlib import Path

from psf_parser.parser import PsfParser
from psf_parser.registry import Datatype, TypeDeclaration, ArrayTypeDeclaration, StructTypeDeclaration, SweepDeclaration, TraceDeclaration, ValueDeclaration
from psf_parser.ascii.token import Tokenizer

class PsfAsciiParser(PsfParser):

    def __init__(self, path: str):
        super().__init__(path)


    def parse(self):
        start_timing = time.time()
        text = Path(self.path).read_text()
        self.timing['FILE_LOAD'] = time.time() - start_timing

        start_timing = time.time()
        self.tokenizer = Tokenizer(text)
        self.timing['TOKENIZE'] = time.time() - start_timing

        self._parse_toc()
        self._validate_toc()

        toc_items = list(self.toc.items())
        for i, (name, start) in enumerate(toc_items):
            stop = toc_items[i + 1][1] if i + 1 < len(toc_items) else len(self.tokenizer.tokens)

            start_timing = time.time()
            match name:
                case 'HEADER':
                    self._parse_header_section(start, stop)
                case 'TYPE':
                    self._parse_type_section(start, stop)
                case 'SWEEP':
                    self._parse_sweep_section(start, stop)
                case 'TRACE':
                    self._parse_trace_section(start, stop)
                case 'VALUE':
                    self._parse_value_section(start, stop)
                case 'END':
                    continue
            self.timing[name] = time.time() - start_timing

        return self


    def _parse_toc(self):
        for i, token in enumerate(self.tokenizer.tokens):
            if token.matches({'KW_HEADER', 'KW_TYPE', 'KW_SWEEP', 'KW_TRACE', 'KW_VALUE', 'KW_END'}):
                if token.value in self.toc.keys():
                    raise SyntaxError(f'Duplicate section {token.value} at {token.row}:{token.column}.')
                self.toc[token.value] = i


    def _parse_header_section(self, start, stop):
        self.tokenizer.goto(start)
        self.tokenizer.next().expect('KW_HEADER')

        while self.tokenizer.position < stop:
            if not self.tokenizer.has_next(2):
                raise SyntaxError('Unexpected end of HEADER section: expected key-value pair.')

            key_token = self.tokenizer.next().expect('STRING')
            value_token = self.tokenizer.next().expect({'STRING', 'INT', 'FLOAT'})
            self.meta[key_token.value] = value_token.value


    def _parse_type_section(self, start, stop):
        self.tokenizer.goto(start)
        self.tokenizer.next().expect('KW_TYPE')

        while self.tokenizer.position < stop:
            self._parse_type_declaration()


    def _parse_sweep_section(self, start, stop):
        self.tokenizer.goto(start)
        self.tokenizer.next().expect('KW_SWEEP')

        while self.tokenizer.position < stop:
            name_token = self.tokenizer.next().expect('STRING')
            type_token = self.tokenizer.next().expect('STRING')

            id = self.registry.generate_unique_id()
            name = name_token.value
            type_id = self.registry.get_by_name(type_token.value).id
            decl = SweepDeclaration(id=id, name=name, type_id=type_id)
            self.registry.add(decl)

            if self.tokenizer.peek().matches('KW_PROP'):
                decl.prop = self._parse_properties()


    def _parse_trace_section(self, start, stop):
        self.tokenizer.goto(start)
        self.tokenizer.next().expect('KW_TRACE')

        while self.tokenizer.position < stop:
            name_token = self.tokenizer.next().expect('STRING')
            type_token = self.tokenizer.next().expect('STRING')

            id = self.registry.generate_unique_id()
            name = name_token.value
            type_id = self.registry.get_by_name(type_token.value).id
            decl = TraceDeclaration(id=id, name=name, type_id=type_id)
            self.registry.add(decl)

            if self.tokenizer.peek().matches('KW_PROP'):
                decl.prop = self._parse_properties()


    def _parse_value_section(self, start, stop):
        self.tokenizer.goto(start)
        self.tokenizer.next().expect('KW_VALUE')

        if 'SWEEP' in self.toc.keys() and 'TRACE' in self.toc.keys():
            while self.tokenizer.position < stop:
                name_token = self.tokenizer.next().expect('STRING')
                decl = self.registry.get_by_name(name_token.value)
                type_decl = decl.get_type()
                decl.data.append(self._parse_value_for_type(type_decl))

        else:
            while self.tokenizer.position < stop:
                name_token = self.tokenizer.next().expect('STRING')
                type_token = self.tokenizer.next().expect('STRING')
                type_decl = self.registry.get_by_name(type_token.value)

                id = self.registry.generate_unique_id()
                name = name_token.value
                type_id = type_decl.id

                decl = ValueDeclaration(id=id, name=name, type_id=type_id)
                decl.data = self._parse_value_for_type(type_decl)
                self.registry.add(decl)

                if self.tokenizer.peek().matches('KW_PROP'):
                    decl.prop = self._parse_properties()


    def _parse_type_declaration(self):
        name_token = self.tokenizer.next().expect('STRING')
        datatype_token = self.tokenizer.next().expect({'KW_STRING', 'KW_INT', 'KW_COMPLEX', 'KW_FLOAT', 'KW_ARRAY', 'KW_STRUCT'})

        id = self.registry.generate_unique_id()
        name = name_token.value
        datatype = Datatype.from_keyword(datatype_token.kind)

        match datatype:
            case dt if dt in {Datatype.STRING, Datatype.INT, Datatype.COMPLEX}:
                decl = TypeDeclaration(id=id, name=name, datatype=datatype)
                self.registry.add(decl)

            case Datatype.FLOAT:
                self.tokenizer.next().expect('KW_DOUBLE')
                decl = TypeDeclaration(id=id, name=name, datatype=datatype)
                self.registry.add(decl)

            case Datatype.ARRAY:
                self.tokenizer.next().expect('LPAREN')  # The format hase '( * )' after ARRAY keyword
                self.tokenizer.next().expect('RPAREN')
                arraytype_token = self.tokenizer.next().expect({'KW_STRING', 'KW_INT', 'KW_FLOAT', 'KW_COMPLEX'})
                arraytype = Datatype.from_keyword(arraytype_token.kind)
                decl = ArrayTypeDeclaration(id=id, name=name, datatype=datatype, arraytype=arraytype)
                self.registry.add(decl)

            case Datatype.STRUCT:
                self.tokenizer.next().expect('LPAREN')
                decl = StructTypeDeclaration(id=id, name=name, datatype=datatype)
                self.registry.add(decl)
                while not self.tokenizer.peek().matches('RPAREN'):
                    member_id = self._parse_type_declaration()
                    decl.members.append(member_id)
                self.tokenizer.next().expect('RPAREN')

        if self.tokenizer.peek().matches('KW_PROP'):
            decl.prop = self._parse_properties()

        return id


    def _parse_properties(self):
        props = {}
        self.tokenizer.next().expect('KW_PROP')
        self.tokenizer.next().expect('LPAREN')
        while not self.tokenizer.peek().matches('RPAREN'):
            key_token = self.tokenizer.next().expect('STRING')
            value_token = self.tokenizer.next().expect({'STRING', 'INT', 'FLOAT'})
            props[key_token.value] = value_token.value
        self.tokenizer.next().expect('RPAREN')
        return props


    def _parse_value_for_type(self, type_decl):
        match type_decl.datatype:
            case dt if dt in {Datatype.STRING, Datatype.INT, Datatype.FLOAT, Datatype.COMPLEX}:
                return self._parse_value_for_datatype(type_decl.datatype)

            case Datatype.ARRAY:
                result = []
                self.tokenizer.next().expect('LPAREN')
                while not self.tokenizer.peek().matches('RPAREN'):
                    result.append(self._parse_value_for_datatype(type_decl.arraytype))
                self.tokenizer.next().expect('RPAREN')
                return result

            case Datatype.STRUCT:
                result = {}
                self.tokenizer.next().expect('LPAREN')
                for member_id in type_decl.members:
                    member = self.registry.get_by_id(member_id)
                    result[member.name] = self._parse_value_for_type(member)
                self.tokenizer.next().expect('RPAREN')
                return result


    def _parse_value_for_datatype(self, datatype):
        match datatype:
            case Datatype.STRING:
                return self.tokenizer.next().expect('STRING').value
            case Datatype.INT:
                return self.tokenizer.next().expect('INT').value
            case Datatype.FLOAT:
                return self.tokenizer.next().expect('FLOAT').value
            case Datatype.COMPLEX:
                raise NotImplementedError()
            case _:
                raise SyntaxError(f'Unexpected basic datatype {datatype}')
