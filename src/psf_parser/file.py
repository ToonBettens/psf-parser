from __future__ import annotations
from typing import Any

from psf_parser.parser import PsfParser
from psf_parser.registry import NonTypeDeclaration, SweepDeclaration, TraceDeclaration, ValueDeclaration


class Signal:
    def __init__(self, name: str, data: Any, quantity: str = '', unit: str = ''):
        self.name = name
        self.data = data
        self.quantity = quantity
        self.unit = unit

    @classmethod
    def from_declaration(cls, decl: NonTypeDeclaration) -> Signal:
        return cls(
            name=decl.name,
            data=decl.data,
            quantity=decl.get_type().name,
            unit=decl.get_type().props.get('unit', ''),
            )

    def __repr__(self):
        return f"<Signal(name='{self.name}', len={len(self.data)})>"


class PsfFile:

    def __init__(self, path: str):
        self.path = path
        self.parser = PsfParser(path).parse()
        self.sweeps = self._collect_signals(SweepDeclaration)
        self.traces = self._collect_signals(TraceDeclaration)
        self.values = self._collect_signals(ValueDeclaration)

    @property
    def signals(self) -> list:
        return self.sweeps | self.traces | self.values

    def _collect_signals(self, cls) -> dict[str, Signal]:
        return {
            decl.name: Signal.from_declaration(decl)
            for decl in self.parser.registry.get_all()
            if isinstance(decl, cls)
        }
