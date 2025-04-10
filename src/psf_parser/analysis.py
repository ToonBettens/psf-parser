from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from psf_parser.file import Signal
from psf_parser.parser import PsfParser




# class OppointAnalysis(Analysis):
#     ...
#
# class DcAnalysis(Analysis):
#     sweeps: dict[str, Signal]
#     traces: dict[str, Signal]
#
#
# class TransientAnalysis(Analysis):
#     ...
#
#
# class SweepAnalysis(Analysis):
#     sweeps: dict[str, Signal]
#     children: list[Analysis]
#
#
# class MonteCarloAnalysis(Analysis):
#     ...
