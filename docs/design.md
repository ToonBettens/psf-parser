# Design

How the library is layered, and why. `format-notes.md` describes the file format itself.

**Status:** this is the design for v1.0. The file layer is in place. The Database is designed here and not built yet.

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

f.header  # dict
f.types  # dict[str, PsfType], the catalogue, kept whole
f.variables  # dict[str, Variable], in file order
f["out"]  # a Variable
f.sweep  # the innermost axis, or None
f.traces  # list[Variable]
f.entries  # list[Variable], standalone values in a file with no sweep

v = f["out"]
v.name, v.type, v.role, v.properties
v.units  # the declaration's, or else the type's
v.values  # the data, read on first access
v.value  # the single value, when there is exactly one
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
| Tagged psfbin | Stops at the value section | One array over the rows, keeping every column |
| Windowed psfbin | Stops at the value section | Block headers, then only that column's run from each block |
| Swept psfascii | Stops at `VALUE` | Tokenizes the rest, whatever was asked for |

### Laziness

Two kinds exist, and both are used.

**File-level:** the Database parses the logFile and defers the rest. Parsing the logFile takes about 1.5 ms, against 32 ms
for all 37 binary files and 66 ms for all 37 ascii files in the test run.

**Value-level:** `load` reads declarations only, so browsing names and units stays cheap. The larger gain is reading one
column from a windowed psfbin file without touching the others, because the values there sit in separate runs per column.
Tagged rows and ascii text interleave their columns, so the first read goes through all of them and keeps them. Reading
one and dropping the rest would save no peak memory, and would cost a full read per column in a loop over all traces.

`load` is always lazy, with no flag, so there is one code path.

No file handle stays open between the phases. `load` remembers the path, and each read opens the file, takes what it needs
and closes it. So there is nothing to close, and nothing stays locked on Windows. A Database spanning thousands of files
needs this anyway, because of the limit on open files.

### When errors surface

Laziness moves some errors later, and these rules keep the cost small:

- **Truncation fails at `load`,** because a whole file ends in `Clarissa` or `END`.
- **A file that changed since `load` fails on the next read,** comparing size and modification time. Otherwise values from a
  new run could sit under the old declarations.
- **Damage inside the values fails on access,** when those values are read, as far as it can be seen at all. A
  changed byte inside a number gives a different number, and PSF has no checksum, so that cannot be detected.

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

A Spectre raw folder opens as a `Database`. Its logFile lists every result and how they nest, so the Database
reads only the logFile at first and parses a data file when its values are asked for.

```python
db = psf_parser.Database("raw/")
print(db)  # every analysis: path, axes, signals
a = db["mysweep/mynestedsweep/ac2"]  # an Analysis
s = a["out"]  # a Signal
s.values.shape  # (3, 3, 61)
[ax.name for ax in s.axes]  # ["R1:r", "C1:c", "freq"]
s.at({"R1:r": 2000})  # the Signal at R1:r = 2k, shape (3, 61)
s[1, 2].file  # the PsfFile behind one point
```

### The objects

| Object | What it is | Main members |
|---|---|---|
| `Database` | One raw folder | `analyses` (path to `Analysis`), `db[path]`, `db.entry(name)`, `str(db)` lists everything |
| `Analysis` | One result tree: an analysis with the sweeps around it | `path`, `entry`, `has_path`, `missing`, `signals` (name to `Signal`), `a[name]` |
| `Signal` | One quantity of an analysis, over all its files | `name`, `units`, `axes`, `values`, `value`, `ragged`, `s[i, j]`, `at({...})`, `fields`, `field(name)`, `files`, `file` |
| `Axis` | One sweep level, or the innermost axis | `name`, `units`, `values`, `parameters`, `len(axis)` |

`db.analyses` and `a.signals` are read-only mappings, as `PsfFile.variables` is at file level.

### Analyses and their paths

The logFile has one tree per result, not one per netlist statement. `mysweep { dc1  ac1  mynestedsweep { ac2 } }`
gives three trees, one for each inner analysis, and a pss gives two, one for its time domain and one for its frequency
domain. Each tree is an `Analysis`.

An analysis is found by its netlist path: the statement names from the outside in, separated by `/`, as in
`mysweep/mynestedsweep/ac2`. Where one analysis writes several kinds of result, the kind follows a `.`, as in
Spectre's file names: `mypss.td`, `mypss.fd`, `mystb.margin`.

The logFile doesn't hold these names on their own. It holds them glued into entry names such as
`mysweep-001_mynestedsweep-002_ac2-ac`, by a rule that is undocumented and has exceptions. So each path is cut from the
names along its tree, and accepted only if the parts glue back into every name Spectre wrote. An analysis that fails
this check, or would share its path with another, keeps its logFile entry name as its path, `has_path` is false, and
the listing says so. A naming case that isn't handled yet thus gives an unexpected name, never another analysis's data.
`db.entry(name)` takes the logFile entry name and always works.

### Signals and axes

A Signal stacks the innermost column of every leaf file into one array. Its axes are the sweep levels from the outside in,
then the innermost axis of the leaf files, so the shape follows the nesting in the netlist.

- **Outer values come from the logFile.** Each child entry carries the value of its parent's sweep as a property. The parent
  sweep file holds the same values with units, but not reliably (format-notes 4), so it only supplies the units, and
  only where its values match the logFile's exactly. Otherwise `units` is `None`.
- **A level can sweep several parameters together.** A paramset sweep varies `rval` and `cval` row by row: three points,
  not a grid. Its axis holds both in `parameters`, and `values` raises, so nobody plots against one of them alone.
- **A value with no inner axis** (a DC operating point, a stability margin) gives a Signal without one: no axes at all on
  its own, or only the sweep axes under a sweep.
- **Struct values** (noise contributions per device, poles) give `fields`, and `field(name)` is again a Signal.
  `fields` is empty for any other Signal, so it also answers whether a Signal is a struct. Strings are numpy object
  arrays, so they keep their shape.

### Indexing, selection and ragged trees

`s[i]` is the Signal at position `i` of the outermost axis, with the remaining axes, and `s[i, j]` goes two levels down.
`s.at({"temp": 27})` selects by value. A value must match a point of that axis up to float rounding: no match, or two,
raises and lists the nearest values. Selection never picks the nearest point and never interpolates, because both answer a
different question than the one asked.

**Ragged trees are common.** Spectre's transient chooses its own time steps, so the transients of a sweep or a Monte
Carlo run usually differ in their time points. No single array holds them honestly. So whether the inner axes agree,
by value and not just by length, decides only whether `s.values` works. Where they differ it raises and says to index
first, `s[0].values` works, and `s.ragged` says so beforehand. Nothing is padded or resampled.

### Partial runs

A killed run leaves a logFile that names files which are missing or truncated. Opening still works. A missing or
unreadable file is a hole, handled like a ragged point: `a.missing` lists them, the points around it can be read, and
`s.values` raises and names the files. A folder without a logFile raises and points to `psf_parser.load`, because
without the logFile the tree and the outer coordinates are gone.

### Back to the file

`s.files` gives the path of every leaf file, shaped like the outer axes. `s.file` gives the loaded `PsfFile` when the
Signal spans exactly one file, and raises otherwise, as `value` does for `values`.

### What is read when

| Call | Reads |
|---|---|
| `Database(folder)` | the logFile |
| `a.signals`, `a[name]` | the declarations of one leaf file |
| `s.axes` | the logFile, and the parent sweep files for units |
| `s.values`, `s[i]`, `s.at(...)` | the leaf files needed, through `psf_parser.load` |

Loaded files keep their columns, and a Signal keeps its stacked array.

---

## Package layout

```
src/psf_parser/
  __init__.py     the public names
  _load.py        load: one file, either encoding
  errors.py       PsfParserError -> PsfParseError, PsfStructureError
  model.py        Kind, Role, PsfType, Variable, PsfFile
  database.py     the Database layer
  _check.py       the rules every parsed file must meet
  _ascii/         tokenizer.py, parser.py
  _binary/        reader.py, chunk.py, parser.py
```

Anything under a leading underscore can change in any release. The parsers are the part most likely to change, because the format has no
specification, and promising less there is what makes a 1.0 promise affordable. Users import from the top level, so `database.py` can be
split later without anyone noticing.
