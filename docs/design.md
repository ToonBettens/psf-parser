# Design

How the library is layered, and why. `format-notes.md` describes the file format itself.

**Status:** this is the design for v1.0, and the code is moving to it. The file layer exists but still has
`PsfBuilder`, `Layout` and eagerly read Python lists. The Database is not built, and its API is not designed yet.

---

## Three layers, by scope

```
open a raw folder  ->  Database      the sweep tree, read from the logFile
                           |          knows: analyses, parents, coordinates
                           v
                       Signal        one named quantity, N-dimensional
                           |          knows: axes, units, which files it spans
                           v
psf_parser.load    ->  PsfFile       one file, faithfully
                                      knows: header, types, variables
```

`PsfFile` answers what is in this file. `Database` answers what this simulation produced. `Signal` bridges
them: it spans files but presents as one thing.

**A signal cannot be built from one file.** In a nested sweep the quantity `out` is spread over nine files:

```
out[R1:r, C1:c, freq]     shape (3, 3, 61)
```

Each leaf file holds only the innermost axis, and the outer coordinates appear only in the logFile
(`format-notes.md` 4.2). So the split between the layers is one of scope, not of taste.

**The database cannot replace the file either.** A file without its logFile still has to be readable, and when a
result looks wrong, you want to look at the one file behind it.

---

## The file layer

```python
f = psf_parser.load("raw/myac.ac")

f.header          # dict
f.types           # dict[str, PsfType], the catalogue, kept whole
f.variables       # dict[str, Variable], in file order
f["out"]          # a Variable
f.sweep           # the innermost axis, or None
f.traces          # list[Variable]
f.entries         # list[Variable], standalone values in a file with no sweep

v = f["out"]
v.name, v.type, v.role, v.properties
v.units           # the declaration's, or else the type's
v.values          # the data, read on first access
v.value           # the single value, when there is exactly one
```

**One `Variable` type at any length.** A 653-point transient trace and a DC operating point differ only in how many
values they hold. Two classes would mean special-casing at every call site.

**No stored file layout.** `f.sweep`, `f.entries` and `len(f)` already say whether a file is a table, named entries or
empty. A stored copy holds no information of its own and could only disagree.

**`properties` is kept verbatim, everywhere.** This format has no specification, and what looks like noise can matter.
The logFile's sweep coordinates live there.

**Declaration ids stay in the parser.** psfbin identifies declarations by numeric id, and psfascii has no such thing.
So ids cannot be part of how a variable is identified, and they live in a symbol table for the duration of the parse.

### Vocabulary

At file level the format's own words are used, because a file is a format artifact: sweep, trace, value. The neutral
container is a `Variable`. A sweep, a trace and a standalone entry are all variables of the file, and none of them is yet
what a user means by a signal. `Signal` is reserved for the Database layer.

### What `values` holds

| Kind | `values` | `value` |
|---|---|---|
| `FLOAT64` | read-only `ndarray`, float64 | `float` |
| `COMPLEX` | read-only `ndarray`, complex128 | `complex` |
| `INT8`, `INT32` | read-only `ndarray`, int8 or int32 | `int` |
| `STRING`, `STRUCT`, `ARRAY` | `list` | the object |

**numpy is required.** A signal of shape (3, 3, 61) is exactly an N-dimensional array, the stdlib has no array of complex
numbers, and someone reading simulation data goes on to do something with it, so they bring numpy in anyway. Decoding
1e6 float64 takes 0.36 ms and 8 MB this way, against 272 ms and 32 MB value by value into a list.

**Arrays are read-only** because they are cached and shared. Writing to one would silently change what every later reader
sees. `.copy()` gives a writable one.

**Arrays are in native byte order.** psfbin is big-endian, and other libraries handle non-native arrays badly.

---

## Reading a file

Parsers work in two phases, at the point where the file itself splits: declarations, then values.

| Arrangement | First phase, at `load` | Second phase, on first access |
|---|---|---|
| Named entries | Reads everything, because declarations sit among the values | Nothing left to do |
| Tagged psfbin | Stops at the value section | One array over the rows, then one field per column |
| Windowed psfbin | Stops at the value section | Block headers, then the column's run from each block |
| Swept psfascii | Stops at `VALUE` | Tokenizes the rest, whatever was asked for |

### Laziness

Two kinds exist, and both are used.

**File-level:** the Database parses the logFile and defers the rest. Parsing the logFile takes about 1.5 ms, against 32 ms
for all 37 binary files and 66 ms for all 37 ascii files in the test run.

**Value-level:** `load` reads declarations only, so browsing names and units stays cheap. The larger gain is reading one
column from a binary file without touching the others. Reading a whole file on first access would not give that, because
asking for one signal would still read every column.

`load` is always lazy, with no flag, so there is one code path.

No file handle stays open between the phases. `load` remembers the path, and each read opens the file, takes what it needs
and closes it. So there is nothing to close, and nothing stays locked on Windows. A Database spanning thousands of files
needs this anyway, because of the limit on open files.

### When errors surface

Laziness moves some errors later, and these rules keep the cost small:

- **Truncation fails at `load`,** because a whole file ends in `Clarissa` or `END`.
- **A file that changed since `load` fails on the next read,** comparing size and modification time. Otherwise values from a
  new run could sit under the old declarations.
- **Damage inside the values fails on access,** when those values are read.

### Errors

Everything raised about a file derives from `PsfParserError`, so a caller walking a folder can write one `except`. Errors about
how the API was used, such as a missing name, stay as the standard `KeyError` and `ValueError`.

- `PsfParseError` means the file could not be read: malformed, truncated or not PSF at all. It is also a `ValueError`, as
  `json.JSONDecodeError` and `tomllib.TOMLDecodeError` are.
- `PsfStructureError` means a file parsed but breaks an invariant the model relies on. This almost always means a parser desynchronised,
  so for a format with no specification, it separates a broken file from a bug in this package.

### The check that matters

A parser reading the wrong number of bytes rarely raises. It desynchronises and produces columns of plausible-looking short
data. So one `check` function holds the rules every file must meet, whichever parser read it: all columns have equal length, and
the row count matches `PSF sweep points` when the header has it. It runs when values arrive, because that is when there is
something to check.

### Two parsers, not one

The parsers are not unified behind a shared source protocol. psfbin has containers, indexes, padding and a table of contents,
and psfascii has a token stream. A protocol over those would be all interface and no substance, on a format with no specification.
They share what they deliver, the model and the `check`, and all format knowledge stays private to each.

---

## The Database layer

Not built yet, and its API is open. What is settled is the idea: open a Spectre raw folder as a database, and get signals out of it.
The rest comes from the format (`format-notes.md` section 4).

Reading a signal walks to the leaves, loads each file and stacks the innermost columns into an N-dimensional array, with the
coordinates collected from the parent chain. Files not reached are never parsed.

### Known risks

**Multi-axis nodes.** `sweepVariable` is an array, and a `paramset` sweep may vary several parameters at once (inferred). It always
holds one name in the current corpus, but a node must be able to contribute several axes.

**Ragged sweeps.** Stacking assumes every leaf shares the innermost axis. An adaptive analysis could give different point counts per
corner, and then no rectangular array exists. Detect this explicitly rather than failing inside numpy.

**Partial runs.** A killed simulation leaves a logFile referencing files that do not exist. Opening the database should still work, and
only access to the missing analysis should fail.

**The tree is a forest, and not fully typed.** Standalone analyses have no `sweep_tree_type`, and neither do Monte Carlo roots, so the
structure has to come from `parent`.

---

## Package layout

```
src/psf_parser/
  __init__.py     the public names
  errors.py       PsfParserError -> PsfParseError, PsfStructureError
  model.py        Kind, Role, PsfType, Variable, PsfFile
  database.py     the Database layer
  _ascii/         tokenizer.py, parser.py
  _binary/        reader.py, chunk.py, parser.py
```

Anything under a leading underscore can change in any release. The parsers are the part most likely to change, because the format has no
specification, and promising less there is what makes a 1.0 promise affordable. Users import from the top level, so `database.py` can be
split later without anyone noticing.
