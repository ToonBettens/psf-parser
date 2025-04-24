from pathlib import Path
from psf_parser.parser import PsfParser

class PsfFile:

    def __init__(self, path: str | Path):
        self.path = str(path)
        self.parser = PsfParser(path).parse()
        self.header = self.parser.header
        self.sweeps = self.parser.registry.sweeps
        self.traces = self.parser.registry.traces
        self.values = self.parser.registry.values

    @property
    def signals(self) -> list:
        return self.sweeps + self.traces + self.values
