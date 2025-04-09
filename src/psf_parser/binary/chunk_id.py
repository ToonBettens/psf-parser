from collections.abc import Iterable

SECTION_HEADER = 0
SECTION_TYPE = 1
SECTION_SWEEP = 2
SECTION_TRACE = 3
SECTION_VALUE = 4

DECLARATION = 16

CONTAINER_META = 19
CONTAINER = 21
CONTAINER_DATA = 22

PROP_STRING = 33
PROP_INT = 34
PROP_FLOAT = 35

section = {SECTION_HEADER, SECTION_TYPE, SECTION_SWEEP, SECTION_TRACE, SECTION_VALUE}
property = {PROP_STRING, PROP_INT, PROP_FLOAT}

def validate(identifier: int, expected: int | Iterable):
    if isinstance(expected, int):
        if identifier != expected:
            raise SyntaxError(f'Invalid identifier: {identifier}. Expected identifier: {expected}')
    elif isinstance(expected, Iterable):
        if identifier not in expected:
            raise SyntaxError(f'Invalid identifier: {identifier}. Expected identifier: {expected}')
    return identifier
