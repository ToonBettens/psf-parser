"""Corpus discovery and test parametrisation."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent / "data"
RUNS_DIR = DATA_DIR / "runs"

# The logFile is psfascii whatever -format the run used, so it is never a binary
# sample and never forms a cross-format pair.
LOGFILE = "logFile"


@dataclass(frozen=True)
class Sample:
    """One PSF file inside a run."""

    run: str
    format: str
    path: Path

    @property
    def id(self) -> str:
        return f"{self.run}/{self.format}/{self.path.name}"


@dataclass(frozen=True)
class Run:
    """One Spectre invocation: a netlist, and its output in one or more formats."""

    name: str
    path: Path

    @property
    def meta(self) -> dict:
        toml = self.path / "run.toml"
        return tomllib.loads(toml.read_text()) if toml.is_file() else {}

    @property
    def formats(self) -> list[str]:
        return sorted(p.name for p in self.path.iterdir() if p.is_dir())

    def samples(self, fmt: str) -> list[Sample]:
        directory = self.path / fmt
        if not directory.is_dir():
            return []
        return [Sample(self.name, fmt, p) for p in sorted(directory.iterdir()) if p.is_file()]

    def logfile(self, fmt: str = "ascii") -> Path | None:
        candidate = self.path / fmt / LOGFILE
        return candidate if candidate.is_file() else None


@lru_cache(maxsize=1)
def all_runs() -> tuple[Run, ...]:
    if not RUNS_DIR.is_dir():
        return ()
    return tuple(Run(p.name, p) for p in sorted(RUNS_DIR.iterdir()) if p.is_dir())


@lru_cache(maxsize=1)
def all_samples() -> tuple[Sample, ...]:
    return tuple(s for run in all_runs() for fmt in run.formats for s in run.samples(fmt))


@lru_cache(maxsize=1)
def all_pairs() -> tuple[tuple[Sample, Sample], ...]:
    """Every file present in both ascii and binary form, as (ascii, binary).

    Unused for now: it exists for differential testing, which is deferred until
    the parser's public objects settle. psfascii is textual and readable by eye,
    so it is the only available oracle for a binary format Cadence has never
    specified.
    """
    pairs = []
    for run in all_runs():
        binaries = {s.path.name: s for s in run.samples("binary")}
        for ascii_sample in run.samples("ascii"):
            if ascii_sample.path.name == LOGFILE:
                continue
            binary_sample = binaries.get(ascii_sample.path.name)
            if binary_sample is not None:
                pairs.append((ascii_sample, binary_sample))
    return tuple(pairs)


@pytest.fixture
def psf_test_files():
    """Legacy corpus root, used by the pre-rewrite tests."""
    return DATA_DIR / "legacy"


def pytest_generate_tests(metafunc):
    if "sample" in metafunc.fixturenames:
        samples = all_samples()
        metafunc.parametrize("sample", samples, ids=[s.id for s in samples])

    if "run" in metafunc.fixturenames:
        runs = all_runs()
        metafunc.parametrize("run", runs, ids=[r.name for r in runs])
