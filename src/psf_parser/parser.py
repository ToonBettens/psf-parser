from __future__ import annotations
from typing import Optional, Literal
from pathlib import Path
from abc import ABC, abstractmethod

from psf_parser.registry import Registry

PsfFormat = Literal['ascii', 'binary']

class PsfParser(ABC):

    def __new__(cls, path: str | Path, format: Optional[PsfFormat] = None):
        if cls is PsfParser:  # Only intercept direct calls to PsfParser
            if format is None:
                format = PsfParser.detect_format(path)
            if format == 'ascii':
                from psf_parser.ascii.parser import PsfAsciiParser
                return super().__new__(PsfAsciiParser)
            elif format == 'binary':
                from psf_parser.binary.parser import PsfBinParser
                return super().__new__(PsfBinParser)
            else:
                raise ValueError(f'Error: Unsupported format - {format}')
        return super().__new__(cls)

    def __init__(self, path: str | Path):
        self.path = path
        self.header = {}
        self.registry = Registry()

    @abstractmethod
    def parse(self) -> PsfParser:
        pass

    @staticmethod
    def detect_format(path: str | Path) -> PsfFormat:
        with open(path, 'rb') as f:
            if f.read(6) == b'HEADER':  # Very naive format detection
                return 'ascii'
            else:
                return 'binary'
