from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional

from psf_parser.registry import Registry

class PsfParser(ABC):

    def __new__(cls, path: str, fmt: Optional[str] = None):
        if cls is PsfParser:  # Only intercept direct calls to PsfParser
            if not fmt:
                fmt = PsfParser.detect_format(path)
            if fmt == 'ascii':
                from psf_parser.ascii.parser import PsfAsciiParser
                return super().__new__(PsfAsciiParser)
            elif fmt == 'binary':
                from psf_parser.binary.parser import PsfBinParser
                return super().__new__(PsfBinParser)
            else:
                raise ValueError(f'Unsupported PSF format: {fmt}')
        return super().__new__(cls)


    def __init__(self, path: str):
        self.path = path
        self.meta = {}
        self.timing = {}
        self.toc = {}
        self.registry = Registry()


    @abstractmethod
    def parse(self) -> PsfParser:
        pass


    @staticmethod
    def detect_format(path: str) -> str:
        """ Very naive format detection """
        with open(path, 'rb') as f:
            if f.read(6) == b'HEADER':
                return 'ascii'
            else:
                return 'binary'


    def _validate_toc(self):
        valid_sequences = [
            ['HEADER', 'TYPE', 'SWEEP', 'TRACE', 'VALUE', 'END'],
            ['HEADER', 'TYPE', 'VALUE', 'END'],
        ]
        section_order = sorted(self.toc.items(), key=lambda item: item[1])
        seen = [key for key, _ in section_order]
        if seen not in valid_sequences:
            raise SyntaxError(f'Invalid section order or combination {seen}.')


    def print_timing_report(self):
        print('\nTiming Report:')
        for section, duration in self.timing.items():
            print(f'  {section:>10}: {duration:.6f} seconds')
