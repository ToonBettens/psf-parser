# Design

How the library is layered, and why. Companion to `format-notes.md`, which describes the
file format itself.

---

## Three layers, by scope

```
psf.open(raw_dir)  ->  Database      the sweep tree, read from logFile
                           |          knows: analyses, parents, coordinates
                           v
                       Signal        one named quantity, N-dimensional
                           |          knows: axes, units, provenance
                           v
psf.load(path)     ->  PsfFile       one file, faithfully
                                      knows: header, types, variables
```

Each layer answers a different question. `PsfFile` answers *what is in this file*.
`Database` answers *what did this simulation produce*. `Signal` bridges them: it spans
files but presents as one thing.

### Why not one layer

A faithful model of one file is small -- three concepts -- and needs no façade over it.
That argues for a single layer, and for a single file it is correct.

It stops being correct at the sweep tree. In a nested sweep the quantity `out` is spread
over nine files:

```
out[R1:r, C1:c, freq]     shape (3, 3, 61)
```

Each leaf file holds only the innermost axis. The outer coordinates -- `R1:r = 1000`,
`C1:c = 2e-06` -- appear **only** in the logFile's properties, never in the data file.
A signal in the sense a user means it therefore cannot be assembled from one file, and
the split between the layers is one of scope rather than of taste.

---

## Layer 1 -- `PsfFile`

```
PsfFile   header: dict
          types: dict[str, PsfType]          the catalogue, kept whole
          variables: dict[str, Variable]     in file order
          shape: Shape                       EMPTY | RECORD | SWEPT

          .sweep    -> Variable | None       the innermost axis
          .traces   -> list[Variable]
          .values   -> list[Variable]        standalone entries
          .rows()                            table iteration

Variable  name, type, role, properties, values
          .units                             declaration overrides type
          .value                             convenience when len == 1
```

Design decisions:

**One `Variable` type at any length.** A 653-point transient trace and a DC operating
point differ only in how many values they hold. Two classes would mean special-casing at
every call site.

**`values` is a property, backed by `_values`.** Nothing lazy sits behind it today. It
exists so that file-level laziness can be added later without changing any call site;
turning an attribute into a property afterwards is the change that would hurt.

**Shape is explicit, decided once at build time.** Files come in four arrangements
(see `format-notes.md` 1.1); collapsing them to `EMPTY | RECORD | SWEPT` and recording
the answer beats inferring it from two accessors at every use.

**`properties` is kept verbatim, everywhere.** This format has no specification, and
what looks like noise today turns out to carry the sweep coordinates the Database needs.

**Parse-time state stays in the parser.** psfbin identifies declarations by numeric id;
psfascii has no such thing. Ids therefore cannot be part of how a variable is identified,
and live in a local symbol table for the duration of the parse.

### Vocabulary

At file level the format's own words are used, because a file *is* a format artifact:
sweep, trace, value. The neutral container is a `Variable` -- a sweep variable, a trace
and a standalone value are all variables of the file, and none of them is yet the
user-facing "signal".

`Signal` is reserved for the Database layer.

---

## Layer 2 -- `Database`

```python
db = psf.open("path/to/raw")  # parses logFile only: ~3 ms

db.analyses  # ['myop', 'myac', 'mysweep_ac2', ...]
db["myac"]  # an Analysis
db["myac"]["out"]  # a Signal

sig = db["mysweep_ac2"]["out"]
sig.axes  # (Axis('R1:r','Ohm'), Axis('C1:c','F'), Axis('freq','Hz'))
sig.shape  # (3, 3, 61)
sig[1000.0, 2e-06]  # the freq trace at that corner
sig.to_numpy()
```

The tree is encoded entirely in the logFile:

| field | meaning |
|---|---|
| `sweep_tree_type` | `sweepNode` (6), `leafNode` (21), or absent (9 standalone) |
| `parent` | links a node to its parent; the structure is a **forest**, not one tree |
| `sweepVariable` | this node's axis, as an ARRAY |
| `PROP` | a leaf's coordinates, e.g. `{'R1:r': 1000.0, 'C1:c': 2e-06}` |
| `dataFile` | which file holds the data |

Reading a signal walks to the leaves, parses each file, and stacks the innermost columns
into an N-dimensional array. Files not reached are never parsed.

### Laziness

Two kinds exist, and only one is worth having.

**File-level** -- parse the logFile, defer the rest. Measured: parsing all 37 files takes
141 ms; the logFile alone takes 2.7 ms. A 50x difference on the common first question,
and it costs the model nothing.

**Value-level** -- read a file's declarations without its values. psfbin makes this
nearly free (the table of contents gives the value section's offset), and psfascii can
stop tokenising at `VALUE` (97% of a transient's bytes). But it only pays when you need
declarations from many files and values from none -- browsing a signal tree, searching a
net name. At 37 files it saves under 100 ms.

Build the first. Keep the option on the second via the `values` property; implement it
only if a use case demands it.

---

## What Layer 1 must guarantee

Layer 2 depends on all of these. They are already true, which is why the file layer can
be frozen before the Database is written.

1. `properties` preserved verbatim -- leaf coordinates live *only* there.
2. The logFile is an ordinary `PsfFile`; no special-casing.
3. Property values keep their type; coordinates are matched by value.
4. Construction from a path is cheap and free of global state.
5. The sweep column is identifiable; it becomes the innermost axis.
6. Units are reachable per variable; axis units come from the sweep declarations.

---

## Known risks in Layer 2

**Multi-axis nodes.** `sweepVariable` is an ARRAY, and Cadence's `paramset` sweeps
several parameters simultaneously. Always one element in the current corpus. A node must
be able to contribute *n* axes.

**Ragged sweeps.** Stacking assumes every leaf shares the innermost axis. An adaptive
analysis could give different point counts per corner, and then no rectangular array
exists. Detect it explicitly rather than failing inside numpy.

**Partial runs.** A killed simulation leaves a logFile referencing files that do not
exist. Opening the database should still work; only access to the missing analysis
should fail.

**Standalone analyses.** Nine entries have no `sweep_tree_type` at all. The structure is
a forest.

**Monte Carlo is structurally a sweep** (`iteration` axis, ordinary node links), so it
needs no special path -- worth re-checking on a larger run.

---

## Package layout

```
src/psf/
  __init__.py     load(), open()
  errors.py       PsfError -> PsfParseError, PsfStructureError
  model.py        Kind, Role, Shape, PsfType, Variable, PsfFile
  builder.py      PsfBuilder -- owns the invariants both parsers respect
  ascii/          tokenizer.py, parser.py
  binary/         reader.py, chunk.py, parser.py
  database/       tree.py, analysis.py, signal.py        (Phase 4)
```

### On the parsers

They are **not** unified behind a shared source protocol. psfbin has containers, indexes,
padding and a table of contents; psfascii has a token stream. A protocol wide enough for
both would be all interface and no substance, and would be debugged through constantly on
a format with no specification.

They share the model, the `Kind` enum, and `PsfBuilder`, which owns the invariants --
notably that a swept file's columns all have the same length. That check catches the
failure mode that matters here: a parser reading the wrong number of bytes does not
crash, it desynchronises and produces short columns that look plausible.

---

## Sequencing

1. Renames, `Shape`, error hierarchy.
2. Point the test suite at `psf`; restore the differential test against `Variable`
   (it is id-free, so it survives).
3. Delete `psf_parser`; rename `psf` -> `psf_parser`. This is the v1.0 break.
4. Build `database/` on the frozen file layer.

Step 3 precedes step 4 deliberately: release and stabilise the file layer before building
the Database on top of something that is still moving.
