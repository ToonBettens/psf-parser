"""The Database layer: a Spectre raw folder read through its logFile."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from types import MappingProxyType
from typing import Any

import numpy as np

from psf_parser._columns import as_column
from psf_parser._load import load
from psf_parser.errors import PsfParseError, PsfParserError
from psf_parser.model import Kind, Properties, PsfFile, Variable

LOGFILE = "logFile"
ENTRY_FIELDS = ("analysisType", "dataFile", "parent", "sweepVariable")
# A sweep level's index inside an entry name: `mysweep-001_ac2` (format-notes 4.3).
INDEX = re.compile(r"-\d+_")
# Statements that only sweep and write no values of their own.
SWEEP_TYPES = ("sweep", "montecarlo")
# The logFile writes coordinates with six significant digits (format-notes 4.2).
LOGFILE_TOLERANCE = 1e-5
# Selecting by value allows for float rounding only.
MATCH_TOLERANCE = 1e-9


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
        self._loaded: dict[str, PsfFile | Exception] = {}
        self._coordinates_of: dict[str, _Coordinates] = {}

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
            counts = tuple(len(node.children) for node in depth_nodes)
            levels.append(_Level(self._level_name(len(levels), parameters), parameters, counts))
            depth_nodes = [child for node in depth_nodes for child in node.children]
        return tuple(levels)

    def _level_name(self, depth: int, parameters: tuple[str, ...]) -> str:
        """A level's parameter, or for several, the statement that sweeps them (or their names joined)."""
        if len(parameters) == 1:
            return parameters[0]
        if depth < len(self._statements):
            return self._statements[depth]
        return ",".join(parameters)

    @cached_property
    def missing(self) -> tuple[Path, ...]:
        """The data files the logFile names for this analysis that don't exist, checked once."""
        return tuple(leaf.data_file for leaf in self._leaves if not leaf.data_file.is_file())

    @cached_property
    def signals(self) -> Mapping[str, Signal]:
        """Every quantity of this analysis by name, read-only.

        The names come from the declarations of the first leaf file that can be read: its traces, or
        its entries when it has no sweep.

        Raises:
            FileNotFoundError: No leaf file of this analysis exists.
            PsfParseError: No leaf file can be read, and the first one exists but is damaged.
        """
        first_error: Exception | None = None
        for leaf in self._leaves:
            file = self._try_load(leaf)
            if isinstance(file, Exception):
                first_error = first_error or file
                continue
            variables = file.traces if file.sweep is not None else file.entries
            return MappingProxyType({v.name: Signal(self, v.name) for v in variables})
        if first_error is not None:
            raise first_error
        return MappingProxyType({})

    def __getitem__(self, name: str) -> Signal:
        try:
            return self.signals[name]
        except KeyError:
            raise KeyError(f"no signal {name!r} in {self.path!r}; available: {', '.join(self.signals)[:200]}") from None

    def _try_load(self, node: _Node) -> PsfFile | Exception:
        """A data file, loaded once, or the error loading it raised."""
        if node.entry not in self._loaded:
            try:
                self._loaded[node.entry] = load(node.data_file)
            except (OSError, PsfParserError) as error:
                self._loaded[node.entry] = error
        return self._loaded[node.entry]

    def _coordinates(self, node: _Node) -> _Coordinates:
        """The coordinates of a node's children, from the logFile and, where it fits, the node's own file."""
        if node.entry in self._coordinates_of:
            return self._coordinates_of[node.entry]
        written: dict[str, np.ndarray] | None = {}
        for parameter in node.sweep_variables:
            column = [child.properties.get(parameter) for child in node.children]
            if any(not isinstance(value, int | float) for value in column):
                written = None
                break
            written[parameter] = _read_only(np.array(column, dtype=float))
        precise, units = self._parent_column(node, written)
        coordinates = _Coordinates(written, precise, units)
        self._coordinates_of[node.entry] = coordinates
        return coordinates

    def _parent_column(
        self, node: _Node, written: dict[str, np.ndarray] | None
    ) -> tuple[np.ndarray | None, str | None]:
        """A sweep file's own column, with its units, when it agrees with the logFile (format-notes 4.5)."""
        if written is None or len(written) != 1:
            return None, None
        ((parameter, values),) = written.items()
        file = self._try_load(node)
        if isinstance(file, Exception) or file.sweep is None or file.sweep.name != parameter:
            return None, None
        try:
            column = file.sweep.values
        except PsfParserError:
            return None, None
        if not isinstance(column, np.ndarray) or column.shape != values.shape or column.dtype.kind not in "iuf":
            return None, None
        if not np.allclose(column, values, rtol=LOGFILE_TOLERANCE, atol=0.0):
            return None, None
        return column, file.sweep.units

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


@dataclass(frozen=True)
class _Coordinates:
    """The coordinates of one sweep node's children.

    Attributes:
        written: Each parameter's values as the logFile writes them, or None when a child lacks one.
        precise: The node's own file's column, when it agrees with `written`.
        units: That column's units.
    """

    written: dict[str, np.ndarray] | None
    precise: np.ndarray | None
    units: str | None


class Axis:
    """One axis of a Signal: a sweep level, or the innermost axis of the leaf files.

    An axis that differs between the points of the axes outside it is ragged: it keeps its name and
    units, and its values raise until those outer axes are indexed.

    Attributes:
        name: The swept parameter, such as `"R1:r"` or `"freq"`, or for a level that sweeps several
            parameters together, the sweep statement's name.
        units: The units, or None where the run doesn't give them reliably.
    """

    def __init__(
        self,
        name: str,
        units: str | None,
        parameters: dict[str, np.ndarray] | None,
        names: tuple[str, ...],
        ragged: str | None = None,
    ):
        self.name = name
        self.units = units
        self._parameters = parameters
        self._names = names
        self._ragged = ragged

    @property
    def parameters(self) -> Mapping[str, np.ndarray]:
        """Each swept parameter's values, one entry per point, read-only.

        Raises:
            ValueError: The axis is ragged.
        """
        if self._parameters is None:
            raise ValueError(f"the {self.name} axis {self._ragged}; index the axes outside it first")
        return MappingProxyType(self._parameters)

    @property
    def values(self) -> np.ndarray:
        """The values at each point, for an axis that sweeps one parameter.

        Raises:
            ValueError: The axis sweeps several parameters together (use `parameters`), or is ragged.
        """
        parameters = self.parameters
        if len(parameters) != 1:
            raise ValueError(f"the {self.name} axis sweeps {', '.join(parameters)} together; use .parameters")
        return next(iter(parameters.values()))

    def __len__(self) -> int:
        return len(next(iter(self.parameters.values())))

    def __repr__(self) -> str:
        units = f" [{self.units}]" if self.units else ""
        size = f"{len(self)} points" if self._parameters is not None else "ragged"
        return f"<Axis {self.name}{units}: {size}>"


@dataclass
class _Layout:
    """How a Signal's leaf files are arranged: every axis, which are kept, and the leaves in order."""

    axes: list[Axis]
    kept: list[int]
    leaves: list[_Node]
    inner: int | None
    problems: list[str]


class Signal:
    """One quantity of an analysis over all its files, such as `out[R1:r, C1:c, freq]`.

    Indexing takes the kept axes in order: `s[1]` is the Signal at the second point of the first axis,
    with the remaining axes. `at()` selects by value on any axis. A struct quantity, such as a noise
    contribution per device, has `fields`, and `field(name)` is again a Signal.

    Attributes:
        name: The quantity's name, as declared in the leaf files.
        analysis: The analysis it belongs to.
    """

    def __init__(self, analysis: Analysis, name: str, picks: Mapping[int, int] | None = None, field: str | None = None):
        self.analysis = analysis
        self.name = name
        self._picks = dict(picks or {})
        self._field = field

    @cached_property
    def _layout(self) -> _Layout:
        analysis = self.analysis
        axes: list[Axis] = []
        kept: list[int] = []
        problems: list[str] = []
        nodes = [analysis._root]
        while any(node.children for node in nodes):
            level = len(axes)
            if not all(node.children for node in nodes):
                swept = next(node for node in nodes if node.children)
                name = analysis._level_name(level, swept.sweep_variables)
                axes.append(Axis(name, None, None, swept.sweep_variables, "is not swept under every outer point"))
                problems.append("its sweep tree is not equally deep everywhere")
                kept.append(level)
                nodes = [leaf for node in nodes for leaf in _leaves_under(node)]
                break
            axes.append(self._level_axis(nodes, level))
            if level in self._picks:
                nodes = [node.children[self._picks[level]] for node in nodes]
            else:
                kept.append(level)
                nodes = [child for node in nodes for child in node.children]

        inner = None
        if nodes and nodes[0].sweep_variables:
            inner = len(axes)
            axes.append(self._inner_axis(nodes, problems))
            if inner not in self._picks:
                kept.append(inner)
        for node in nodes:
            problem = self._hole(node)
            if problem:
                problems.append(problem)
        return _Layout(axes, kept, nodes, inner, problems)

    def _level_axis(self, nodes: list[_Node], level: int) -> Axis:
        """The axis of one sweep level, from every node at that depth."""
        parameters = nodes[0].sweep_variables
        name = self.analysis._level_name(level, parameters)
        if any(node.sweep_variables != parameters for node in nodes):
            return Axis(name, None, None, parameters, "sweeps different parameters under different outer points")
        coordinates = [self.analysis._coordinates(node) for node in nodes]
        written = [c.written for c in coordinates if c.written is not None]
        if len(written) != len(coordinates):
            return Axis(name, None, None, parameters, "has no coordinates in the logFile")
        first = written[0]
        if any(not _same_columns(first, w) for w in written[1:]):
            return Axis(name, None, None, parameters, "differs between the points of the axes outside it")
        precise = [c.precise for c in coordinates if c.precise is not None]
        units = {c.units for c in coordinates}
        agree = len(precise) == len(coordinates) and all(np.array_equal(p, precise[0]) for p in precise)
        if agree and len(units) == 1:
            return Axis(name, units.pop(), {parameters[0]: precise[0]}, parameters)
        return Axis(name, None, first, parameters)

    def _inner_axis(self, leaves: list[_Node], problems: list[str]) -> Axis:
        """The innermost axis, shared by every leaf file that can be read, or ragged."""
        name = leaves[0].sweep_variables[0]
        columns = []
        units = None
        for leaf in leaves:
            file = self.analysis._try_load(leaf)
            if isinstance(file, Exception) or file.sweep is None:
                continue
            try:
                column = file.sweep.values
            except PsfParserError as error:
                problems.append(f"{leaf.data_file.name} can't be read ({error})")
                continue
            if isinstance(column, np.ndarray):
                columns.append(column)
                units = file.sweep.units
        if not columns:
            return Axis(name, None, None, (name,), "could not be read from any leaf file")
        first = columns[0]
        if any(len(c) != len(first) or not np.array_equal(c, first) for c in columns[1:]):
            lengths = sorted({len(c) for c in columns})
            detail = f" ({lengths[0]} to {lengths[-1]} points)" if len(lengths) > 1 else ""
            return Axis(name, units, None, (name,), f"differs between the leaf files{detail}")
        return Axis(name, units, {name: first}, (name,))

    def _hole(self, leaf: _Node) -> str | None:
        """Why a leaf can't give this Signal's values, or None."""
        if leaf.is_empty_sweep:
            return f"{leaf.entry} holds no results"
        file = self.analysis._try_load(leaf)
        if isinstance(file, FileNotFoundError):
            return f"{leaf.data_file.name} is missing"
        if isinstance(file, Exception):
            return f"{leaf.data_file.name} can't be read ({file})"
        if self.name not in file:
            return f"{leaf.data_file.name} has no {self.name!r}"
        if self._field is not None and self._field not in _field_names(file[self.name]):
            return f"{leaf.data_file.name} has no field {self._field!r} in {self.name!r}"
        return None

    @property
    def axes(self) -> tuple[Axis, ...]:
        """The remaining axes, outermost first: the sweep levels, then the leaf files' own sweep."""
        layout = self._layout
        return tuple(layout.axes[k] for k in layout.kept)

    @property
    def ragged(self) -> bool:
        """Whether `values` would fail: an axis differs between outer points, or a leaf file is missing."""
        return bool(self._problems())

    def _problems(self) -> list[str]:
        layout = self._layout
        ragged_axes = [
            f"the {layout.axes[k].name} axis {layout.axes[k]._ragged}" for k in layout.kept if layout.axes[k]._ragged
        ]
        return ragged_axes + layout.problems

    def _declaration(self) -> Variable | None:
        """The quantity as the first leaf file that can be read declares it."""
        for leaf in self._layout.leaves:
            file = self.analysis._try_load(leaf)
            if not isinstance(file, Exception) and self.name in file:
                return file[self.name]
        return None

    @cached_property
    def units(self) -> str | None:
        """The units of the quantity, or of the field, from the first leaf file that can be read."""
        variable = self._declaration()
        if variable is None:
            return None
        if self._field is None:
            return variable.units
        return next((f.units for f in variable.type.fields if f.name == self._field), None)

    @cached_property
    def fields(self) -> tuple[str, ...]:
        """The field names of a struct quantity, in declared order, and empty for any other."""
        variable = self._declaration()
        if variable is None or self._field is not None:
            return ()
        return _field_names(variable)

    def field(self, name: str) -> Signal:
        """One field of a struct quantity, over the same axes.

        Args:
            name: A field name from `fields`, such as `"rn"` for a noise contribution.

        Returns:
            The field as a Signal of its own.

        Raises:
            KeyError: The quantity has no field of that name.
        """
        if name not in self.fields:
            raise KeyError(f"{self.name!r} has no field {name!r}; fields: {', '.join(self.fields) or 'none'}")
        return Signal(self.analysis, self.name, self._picks, name)

    @cached_property
    def values(self) -> np.ndarray:
        """Every value as one read-only array, shaped like the axes.

        Numbers come as numeric arrays, strings as object arrays of the same shape.

        Raises:
            ValueError: The quantity is a struct (use `field()`), or the Signal is ragged; the message
                names the reason, and indexing the outer axes first gives Signals that aren't.
            PsfParseError: A leaf file's values are damaged.
        """
        if self.fields:
            raise ValueError(f"{self.name!r} is a struct with fields {', '.join(self.fields)}; use .field(name)")
        problems = self._problems()
        if problems:
            hint = "; index the outer axes first, such as s[0]" if len(self.axes) > 1 else ""
            raise ValueError(f"{self.name!r} in {self.analysis.path!r} is not one array: {'; '.join(problems)}{hint}")
        layout = self._layout
        columns = []
        for leaf in layout.leaves:
            file = self.analysis._try_load(leaf)
            assert not isinstance(file, Exception)
            column = self._column(file[self.name])
            if layout.inner is None:
                column = column[0]
            elif layout.inner in self._picks:
                column = column[self._picks[layout.inner]]
            columns.append(column)
        shape = tuple(len(layout.axes[k]) for k in layout.kept)
        if len(columns) == 1 and isinstance(columns[0], np.ndarray):
            # One leaf: a view of the file's own column, so it isn't held twice.
            return _read_only(columns[0].reshape(shape))
        if all(isinstance(column, np.ndarray | np.generic) and column.dtype != object for column in columns):
            return _read_only(np.array(columns).reshape(shape))
        stacked = np.empty((len(columns), *np.shape(columns[0])), dtype=object)
        for index, column in enumerate(columns):
            stacked[index] = column
        return _read_only(stacked.reshape(shape))

    def _column(self, variable: Variable) -> np.ndarray:
        """This Signal's column of one leaf file, as an array: a field's values for a struct."""
        if self._field is None:
            values = variable.values
        else:
            kind = next(f.kind for f in variable.type.fields if f.name == self._field)
            values = as_column(kind, [item[self._field] for item in variable.values])
        if isinstance(values, np.ndarray):
            return values
        objects = np.empty(len(values), dtype=object)
        for index, value in enumerate(values):
            objects[index] = value
        return objects

    @property
    def value(self) -> Any:
        """The single value, when the Signal holds exactly one.

        Raises:
            ValueError: It holds more than one value.
        """
        values = self.values
        if values.size != 1:
            raise ValueError(f"{self.name!r} holds {values.size} values; use .values")
        return values.item()

    @property
    def files(self) -> np.ndarray:
        """The path of every leaf file, shaped like the outer axes, including files that are missing.

        Raises:
            ValueError: An outer axis is ragged, so the paths have no common shape.
        """
        layout = self._layout
        outer = [k for k in layout.kept if k != layout.inner]
        if any(layout.axes[k]._ragged for k in outer) or len(layout.leaves) != _product(
            len(layout.axes[k]) for k in outer
        ):
            raise ValueError(f"the files of {self.name!r} have no common shape; index the outer axes first")
        paths = np.empty(len(layout.leaves), dtype=object)
        paths[:] = [leaf.data_file for leaf in layout.leaves]
        return paths.reshape(tuple(len(layout.axes[k]) for k in outer))

    @property
    def file(self) -> PsfFile:
        """The loaded file behind this Signal, when it spans exactly one.

        Raises:
            ValueError: The Signal spans several files.
            FileNotFoundError: The file is missing.
            PsfParseError: The file can't be read.
        """
        leaves = self._layout.leaves
        if len(leaves) != 1:
            raise ValueError(f"{self.name!r} spans {len(leaves)} files; index the outer axes first, or use .files")
        file = self.analysis._try_load(leaves[0])
        if isinstance(file, Exception):
            raise file
        return file

    def __getitem__(self, key: int | tuple[int, ...]) -> Signal:
        positions = key if isinstance(key, tuple) else (key,)
        kept = self._layout.kept
        if len(positions) > len(kept):
            raise IndexError(f"{self.name!r} has {len(kept)} axes; got {len(positions)} indices")
        picks = dict(self._picks)
        for level, position in zip(kept, positions, strict=False):
            if not isinstance(position, int | np.integer) or isinstance(position, bool):
                raise TypeError(f"index a Signal with integers, not {type(position).__name__}; slice .values instead")
            picks[level] = self._checked_position(level, int(position))
        return Signal(self.analysis, self.name, picks, self._field)

    def at(self, selection: Mapping[str, float]) -> Signal:
        """The Signal at given values of some of its axes, matched to within float rounding.

        Args:
            selection: Axis or parameter names, such as `{"R1:r": 2000}`, each with one value. For an axis
                that sweeps several parameters, any one of them selects the point.

        Returns:
            The Signal without the selected axes.

        Raises:
            KeyError: A name is not an axis or parameter of this Signal.
            ValueError: A value matches no point or several, or its axis is ragged.
        """
        signal = self
        for name, target in selection.items():
            layout = signal._layout
            level = next((k for k in layout.kept if name == layout.axes[k].name or name in layout.axes[k]._names), None)
            if level is None:
                names = ", ".join(layout.axes[k].name for k in layout.kept)
                raise KeyError(f"no axis or parameter {name!r} in {self.name!r}; axes: {names}")
            axis = layout.axes[level]
            parameters = axis.parameters
            values = parameters.get(name)
            if values is None:
                values = axis.values
            position = _match(name, values, target)
            picks = dict(signal._picks)
            picks[level] = position
            signal = Signal(self.analysis, self.name, picks, self._field)
        return signal

    def _checked_position(self, level: int, position: int) -> int:
        axis = self._layout.axes[level]
        size = len(axis)
        if not -size <= position < size:
            raise IndexError(f"index {position} is out of range for the {axis.name} axis of {size} points")
        return position % size

    def __repr__(self) -> str:
        field = f" field {self._field}" if self._field else ""
        units = f" [{self.units}]" if self.units else ""
        axes = ", ".join(axis.name for axis in self.axes)
        return f"<Signal {self.name}{field}{units}: {axes or 'no axes'}>"


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


def _leaves_under(node: _Node) -> list[_Node]:
    """Every entry without children under a node, in logFile order."""
    if not node.children:
        return [node]
    return [leaf for child in node.children for leaf in _leaves_under(child)]


def _same_columns(a: dict[str, np.ndarray], b: dict[str, np.ndarray]) -> bool:
    return a.keys() == b.keys() and all(np.array_equal(a[name], b[name]) for name in a)


def _product(sizes) -> int:
    result = 1
    for size in sizes:
        result *= size
    return result


def _read_only(array: np.ndarray) -> np.ndarray:
    array.setflags(write=False)
    return array


def _match(name: str, values: np.ndarray, target: float) -> int:
    """The one position where an axis has the target value, to within float rounding."""
    hits = np.flatnonzero(np.isclose(values, target, rtol=MATCH_TOLERANCE, atol=0.0))
    if len(hits) == 1:
        return int(hits[0])
    nearest = values[np.argsort(np.abs(values - target), kind="stable")[:3]]
    found = "no point matches" if len(hits) == 0 else f"{len(hits)} points match"
    listed = ", ".join(f"{value:g}" for value in nearest)
    raise ValueError(f"{name} = {target:g}: {found}; nearest: {listed}")


def _field_names(variable: Variable) -> tuple[str, ...]:
    """The field names of a struct variable, and empty for any other."""
    if variable.type.kind is not Kind.STRUCT:
        return ()
    return tuple(f.name for f in variable.type.fields)
