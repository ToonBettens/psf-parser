"""The Database layer: a Spectre raw folder read through its logFile."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from types import MappingProxyType

from psf_parser._load import load
from psf_parser.errors import PsfParseError
from psf_parser.model import Properties

LOGFILE = "logFile"
ENTRY_FIELDS = ("analysisType", "dataFile", "parent", "sweepVariable")
# A sweep level's index inside an entry name: `mysweep-001_ac2` (format-notes 4.3).
INDEX = re.compile(r"-\d+_")
# Statements that only sweep and write no values of their own.
SWEEP_TYPES = ("sweep", "montecarlo")


@dataclass(eq=False)
class _Node:
    """One logFile entry, linked to the entries under it."""

    entry: str
    analysis_type: str
    data_file: Path
    parent: str
    sweep_variables: tuple[str, ...]
    properties: Properties
    children: list[_Node] = field(default_factory=list)

    @property
    def stem(self) -> str:
        """The entry name without its `-<analysisType>` suffix."""
        suffix = f"-{self.analysis_type}"
        return self.entry.removesuffix(suffix) if self.entry.endswith(suffix) else ""

    @property
    def is_empty_sweep(self) -> bool:
        """A sweep with no entries under it, so no result is linked to it (format-notes 4.4)."""
        sweep_node = str(self.properties.get("sweep_tree_type", "")).lower().endswith("sweepnode")
        return not self.children and (sweep_node or self.analysis_type in SWEEP_TYPES)


@dataclass(frozen=True)
class _Level:
    """One sweep level of an analysis, from the outside in.

    Attributes:
        name: The statement name for a level that sweeps several parameters, else the parameter.
        parameters: The swept parameters, as the logFile names them.
        counts: How many points each node at this level has.
    """

    name: str
    parameters: tuple[str, ...]
    counts: tuple[int, ...]


class Analysis:
    """One result tree of a raw folder: an analysis with the sweeps around it.

    Attributes:
        path: The netlist path, such as `"mysweep/mynestedsweep/ac2"`, or the entry name when it
            can't be derived safely.
        entry: The logFile entry name of the tree's root, such as `"mysweep_ac2-sweep"`.
        has_path: Whether `path` is a netlist path rather than the entry name.
    """

    def __init__(self, root: _Node, path: str | None, statements: tuple[str, ...]):
        self._root = root
        self._statements = statements
        self.entry = root.entry
        self.has_path = path is not None
        self.path = path if path is not None else root.entry

    @cached_property
    def _leaves(self) -> tuple[_Node, ...]:
        """The entries that hold data, in logFile order."""
        leaves: list[_Node] = []
        pending = [self._root]
        while pending:
            node = pending.pop()
            if node.children:
                pending.extend(reversed(node.children))
            elif not node.is_empty_sweep:
                leaves.append(node)
        return tuple(leaves)

    @cached_property
    def _levels(self) -> tuple[_Level, ...]:
        """The sweep levels from the outside in, without the innermost axis of the leaf files."""
        levels = []
        depth_nodes = [self._root]
        while depth_nodes and all(node.children for node in depth_nodes):
            parameters = depth_nodes[0].sweep_variables
            name = parameters[0] if len(parameters) == 1 else self._level_name(len(levels), parameters)
            counts = tuple(len(node.children) for node in depth_nodes)
            levels.append(_Level(name, parameters, counts))
            depth_nodes = [child for node in depth_nodes for child in node.children]
        return tuple(levels)

    def _level_name(self, depth: int, parameters: tuple[str, ...]) -> str:
        if depth < len(self._statements):
            return self._statements[depth]
        return ",".join(parameters)

    @cached_property
    def missing(self) -> tuple[Path, ...]:
        """The data files the logFile names for this analysis that don't exist, checked once."""
        return tuple(leaf.data_file for leaf in self._leaves if not leaf.data_file.is_file())

    def _describe(self) -> str:
        """The axes as far as the logFile knows them: each sweep level with its length, then the inner axis."""
        parts = []
        for level in self._levels:
            low, high = min(level.counts), max(level.counts)
            parts.append(f"{level.name} ({low})" if low == high else f"{level.name} ({low}-{high})")
        inner = {leaf.sweep_variables for leaf in self._leaves}
        if len(inner) == 1:
            parts.extend(next(iter(inner)))
        elif inner:
            parts.append("?")
        return ", ".join(parts)

    def __repr__(self) -> str:
        return f"<Analysis {self.path}>"


class Database:
    """A Spectre raw folder, opened through its logFile.

    Opening reads the logFile only. Data files are read when their values are asked for.

    Attributes:
        folder: The raw folder.
        analyses: Every analysis by its path, in logFile order. Read-only.
    """

    def __init__(self, folder: str | Path):
        """Read the logFile of a raw folder and derive the path of every analysis.

        Args:
            folder: The folder Spectre wrote with `-raw`, holding a `logFile`.

        Raises:
            FileNotFoundError: The folder has no logFile.
            PsfParseError: The logFile is damaged, or its entries lack the fields of an analysis.
        """
        self.folder = Path(folder)
        logfile = self.folder / LOGFILE
        if not logfile.is_file():
            raise FileNotFoundError(f"{self.folder} has no {LOGFILE}; read single files with psf_parser.load")

        nodes = {}
        for variable in load(logfile):
            entry = variable.value
            if not isinstance(entry, dict) or any(name not in entry for name in ENTRY_FIELDS):
                raise PsfParseError(f"{logfile}: entry {variable.name!r} lacks the fields of an analysis")
            nodes[variable.name] = _Node(
                entry=variable.name,
                analysis_type=str(entry["analysisType"]),
                data_file=self.folder / str(entry["dataFile"]),
                parent=str(entry["parent"]),
                sweep_variables=tuple(str(name) for name in entry["sweepVariable"]),
                properties=variable.properties,
            )
        self._nodes = nodes

        roots = []
        for node in nodes.values():
            # A parent missing from the logFile makes its child a root of its own.
            parent = nodes.get(node.parent) if node.parent else None
            if parent is None:
                roots.append(node)
            else:
                parent.children.append(node)

        derived = {root.entry: _derive_path(root) for root in roots}
        paths = _unique_paths({entry: found[0] if found else None for entry, found in derived.items()})
        analyses = {}
        for root in roots:
            found = derived[root.entry]
            path = paths[root.entry]
            statements = found[1] if found and path is not None else ()
            analysis = Analysis(root, path, statements)
            analyses[analysis.path] = analysis
        self.analyses: Mapping[str, Analysis] = MappingProxyType(analyses)
        self._by_entry = {analysis.entry: analysis for analysis in analyses.values()}

    def __getitem__(self, path: str) -> Analysis:
        try:
            return self.analyses[path]
        except KeyError:
            hint = "; use db.entry() for a logFile entry name" if path in self._nodes else ""
            raise KeyError(f"no analysis {path!r}{hint}; available: {', '.join(self.analyses)[:200]}") from None

    def entry(self, name: str) -> Analysis:
        """The analysis whose tree root has this logFile entry name.

        Args:
            name: An entry name from the logFile, such as `"mysweep_ac2-sweep"`.

        Returns:
            The analysis rooted at that entry.

        Raises:
            KeyError: No root entry has that name. The message names the root when it is an entry inside a tree.
        """
        if name in self._by_entry:
            return self._by_entry[name]
        node = self._nodes.get(name)
        if node is None:
            raise KeyError(f"no logFile entry {name!r}")
        while node.parent in self._nodes:
            node = self._nodes[node.parent]
        raise KeyError(f"{name!r} is inside the analysis {self._by_entry[node.entry].path!r}, rooted at {node.entry!r}")

    def __str__(self) -> str:
        width = max((len(path) for path in self.analyses), default=0)
        lines = [f"Database {self.folder}: {len(self.analyses)} analyses"]
        for path, analysis in self.analyses.items():
            note = "" if analysis.has_path else "(entry name, no netlist path)"
            detail = " ".join(part for part in (analysis._describe(), note) if part)
            lines.append(f"  {path:<{width}}   {detail}".rstrip())
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"<Database {self.folder}: {len(self.analyses)} analyses>"


def _derive_path(root: _Node) -> tuple[str, tuple[str, ...]] | None:
    """The netlist path of a tree and its statement names, or None when its entry names don't fit.

    The names along the tree are cut into statement names at each level's index, and the result is
    accepted only if every entry name in the tree glues back from those parts (format-notes 4.3).
    """
    chain = [root]
    while chain[-1].children:
        chain.append(chain[-1].children[0])
    leaf = chain[-1]
    if leaf.is_empty_sweep or not leaf.stem:
        return None

    # A level that repeats the analysis type is the analysis's own (pac sidebands): its entries add `.<value>`.
    # Any other level is a sweep statement, whose entries add `-<index>_`.
    sweeps = sum(1 for node in chain[:-1] if node.analysis_type != leaf.analysis_type)
    own_levels = len(chain) - 1 - sweeps
    base = leaf.stem.rsplit(".", own_levels)[0] if own_levels else leaf.stem
    statements = INDEX.split(base)
    if len(statements) != sweeps + 1 or not all(statements):
        return None
    kind = leaf.analysis_type.rpartition(".")[0]

    if not _fits(root, [], statements, leaf.analysis_type, kind):
        return None
    path = "/".join(statements)
    return (f"{path}.{kind}" if kind else path), tuple(statements[:-1])


def _fits(node: _Node, above: list[_Node], statements: list[str], leaf_type: str, kind: str) -> bool:
    """Whether a node's entry name and those of everything under it glue back from the statement names."""
    sweeps_above = sum(1 for n in above if n.analysis_type != leaf_type)
    own_above = len(above) - sweeps_above
    prefix = "".join(rf"{re.escape(name)}-\d+_" for name in statements[:sweeps_above])
    analysis = re.escape(statements[-1])
    if node.children and node.analysis_type != leaf_type:
        if sweeps_above >= len(statements) - 1:
            return False
        # A swept pss adds its kind to the sweep's entries: `mysweep_pss2_td` (format-notes 4.3).
        kind_suffix = rf"(_{re.escape(kind)})?" if kind else ""
        pattern = prefix + re.escape(statements[sweeps_above]) + "_" + analysis + kind_suffix
    else:
        if node.analysis_type != leaf_type or sweeps_above != len(statements) - 1:
            return False
        pattern = prefix + analysis + r"\.[^.]+" * own_above
    if not re.fullmatch(pattern, node.stem):
        return False
    return all(_fits(child, [*above, node], statements, leaf_type, kind) for child in node.children)


def _unique_paths(candidates: dict[str, str | None]) -> dict[str, str | None]:
    """Drop every derived path that another analysis shares, as a derived path or as an entry name."""
    paths = dict(candidates)
    while True:
        counts = Counter(path if path is not None else entry for entry, path in paths.items())
        clashing = [entry for entry, path in paths.items() if path is not None and counts[path] > 1]
        if not clashing:
            return paths
        for entry in clashing:
            paths[entry] = None
