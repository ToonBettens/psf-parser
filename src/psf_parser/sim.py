from __future__ import annotations
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from psf_parser.file import Signal
from psf_parser.parser import PsfParser
from psf_parser.registry import SweepDeclaration, TraceDeclaration, ValueDeclaration

dataclass_kw = dataclass(kw_only=True)

@dataclass_kw
class Simulation:
    name: str
    path: str
    timestamp: str
    description: str
    simulator: str
    simulator_version: str
    analyses: dict[str, Analysis] = field(default_factory=dict)

    @property
    def id(self):
        time_str = self.timestamp.strftime('%Y%m%d_%H%M%S')
        return f'{self.name}_{time_str}'

    @classmethod
    def from_raw(cls, name: str, path: str):
        logfile = Path(path) / 'logFile'
        if not logfile.is_file():
            raise Exception()

        parser = PsfParser(logfile).parse()

        sim = cls(
            name = name,
            path = path,
            timestamp = datetime.strptime(parser.meta['date'], '%I:%M:%S %p, %a %b %d, %Y'),
            description = parser.meta['design'],
            simulator = parser.meta['simulator'],
            simulator_version = parser.meta['version']
        )

        analyses_by_id = {}
        for decl in parser.registry.get_by_group(ValueDeclaration):
            analysis = AnalysisProxy(
                name = decl.data['dataFile'].split('.')[0],
                kind = decl.data['analysisType'],
                path = decl.data['dataFile'],
                simulation = sim
            )
            analyses_by_id[analysis.id] = analysis

            parent = decl.data['parent']
            if parent == '':
                sim.analyses[analysis.path] = analysis
            else:
                analyses_by_id[parent]._children.append(analysis)

        return sim

    def __repr__(self):
        return (
            f"<Simulation(name='{self.name}', analyses={list(self.analyses)})>"
        )


@dataclass_kw
class Analysis:
    name: str
    kind: str
    path: str
    simulation: Optional[Simulation] = None

    @property
    def id(self):
        return self.path.replace('.', '-')

    def __repr__(self):
        return f"<Analysis(name='{self.name}', kind='{self.kind}')>"

@dataclass_kw
class OppointAnalysis(Analysis):
    ...


@dataclass_kw
class DcAnalysis(Analysis):
    sweeps: dict[str, Signal] = field(default_factory=dict)
    traces: dict[str, Signal] = field(default_factory=dict)

    def __repr__(self):
        return f"<DcAnalysis(name='{self.name}', sweeps={len(self.sweeps)}, traces={len(self.traces)})>"


@dataclass_kw
class SweepAnalysis(Analysis):
    sweeps: dict[str, Signal] = field(default_factory=dict)
    children: list[Analysis] = field(default_factory=dict)

    def __repr__(self):
        return f"<SweepAnalysis(name='{self.name}', sweeps={len(self.sweeps)}, children={len(self.children)})>"


class AnalysisProxy(Analysis):

    def __init__(self, name: str, kind: str, path: str, simulation: Optional[Simulation] = None):
        super().__init__(name=name, kind=kind, path=path, simulation=simulation)
        self._loaded = False
        self._analysis: Optional[Analysis] = None
        self._children: list[AnalysisProxy] = []

    def __repr__(self):
        if self._loaded:
            return self._analysis.__repr__()
        else:
            return f"<AnalysisProxy(name='{self.name}', kind='{self.kind}')"

    def _load(self):
        if not self._loaded:
            path = Path(self.simulation.path) / self.path
            parser = PsfParser(path).parse()

            match self.kind:
                case 'dc':
                    self._analysis = DcAnalysis(
                        name = self.name,
                        kind = self.kind,
                        path = self.path,
                        simulation = self.simulation,
                        sweeps = self._collect_signals(parser, SweepDeclaration),
                        traces = self._collect_signals(parser, TraceDeclaration),
                    )
                case 'sweep':
                    self._analysis = SweepAnalysis(
                        name = self.name,
                        kind = self.kind,
                        path = self.path,
                        simulation = self.simulation,
                        sweeps = self._collect_signals(parser, SweepDeclaration),
                        children = self._children,
                    )
                case _:
                    raise NotImplementedError()

            self._loaded = True

    def _collect_signals(self, parser, cls) -> dict[str, Signal]:
        return {
            decl.name: Signal.from_declaration(decl)
            for decl in parser.registry.get_by_group(cls)
        }

    def __getattr__(self, attr):
        # If attr wasn't part of AnalysisProxy, load Analysis and pass attribute from there
        self._load()
        if attr == 'children':
            return self._children
        return getattr(self._analysis, attr)

    def __dir__(self):
        base = super().__dir__()
        if not self._loaded:
            return base

        loaded_attrs = dir(self._analysis)
        return sorted(set(base + loaded_attrs))
