import re

keywords = {
    'KW_HEADER': 'HEADER',
    'KW_TYPE': 'TYPE',
    'KW_SWEEP': 'SWEEP',
    'KW_TRACE': 'TRACE',
    'KW_VALUE': 'VALUE',
    'KW_END': 'END',
    'KW_STRING': 'STRING',
    'KW_INT': 'INT',
    'KW_FLOAT': 'FLOAT',
    'KW_DOUBLE': 'DOUBLE',
    'KW_COMPLEX': 'COMPLEX',
    'KW_ARRAY': 'ARRAY',
    'KW_STRUCT': 'STRUCT',
    'KW_PROP': 'PROP',
}

token_specification = [
    ('STRING', r'"(?:\\.|[^"\\])*"'),
    ('FLOAT', r'[+-]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?'),
    ('INT', r'[+-]?[0-9]+'),
    ('ID', r'[A-Z]+'),
    ('LPAREN', r'\('),
    ('RPAREN', r'\)'),
    ('SKIP', r'[\s*]+'),
    ('MISMATCH', r'.'),
]

tok_regex = re.compile(
    '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
)


class Token:
    __slots__ = ('kind', 'value', 'row', 'column')

    def __init__(self, kind, value, row, column):
        self.kind = kind
        self.value = value
        self.row = row
        self.column = column

    def __repr__(self):
        return f'Token({self.kind!r}, {self.value!r}, {self.row}, {self.column})'

    def matches(self, kinds, value=None):
        if isinstance(kinds, (list, tuple, set)):
            kind_match = self.kind in kinds
        else:
            kind_match = self.kind == kinds

        if value is None:
            return kind_match
        elif callable(value):
            return kind_match and value(self.value)
        elif isinstance(value, (list, tuple, set)):
            return kind_match and self.value in value
        else:
            return kind_match and self.value == value

    def expect(self, kinds, value=None):
        if not self.matches(kinds, value):
            raise SyntaxError(f'[{repr(self)}] Expected kind {kinds!r} with value {value!r}.')
        return self

    def is_keyword(self):
        return self.kind in keywords.keys()


class Tokenizer:
    def __init__(self, text: str):
        self.text = text
        self.tokens = list(self._generate_tokens())
        self.position = 0

    def _generate_tokens(self):
        row = 1
        column = 1

        for mo in tok_regex.finditer(self.text):
            kind = mo.lastgroup
            value = mo.group(kind)
            token_length = len(value)

            # Skip whitespace
            if kind == 'SKIP':
                for i, char in enumerate(value):
                    if char == '\n':
                        row += 1
                        column = 1
                    else:
                        column += 1
                continue
            elif kind == 'MISMATCH':
                raise SyntaxError(f"Unexpected character '{value}' at position ({row}, {column})")
            elif kind == 'STRING':
                value = value[1:-1]  # Remove the quotes
            elif kind == 'FLOAT':
                value = float(value)
            elif kind == 'INT':
                value = int(value)
            elif kind == 'ID':
                upper_val = value.upper()
                for kw_code, kw_string in keywords.items():
                    if upper_val == kw_string:
                        kind = kw_code
                        break

            yield Token(kind, value, row, column)
            column += token_length

    def goto(self, position=0):
        self.position = position

    def has_next(self, n = 1):
        return self.position + n <= len(self.tokens)

    def peek(self):
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return None

    def next(self):
        token = self.peek()
        self.position += 1
        return token
