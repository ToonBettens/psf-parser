# PSF format notes

Cadence has never published a specification for PSF. Everything here was derived by reading
files that Spectre produced, and by cross-checking the two encodings of the same simulation.
All of it is observed, not specified. Where something is only inferred, it says so.

Corpus behind these notes: one Spectre 23.1 run of an RC low-pass filter, `psfversion 1.4.0`,
written as both psfascii and psfbin (`tests/data/runs/rc_lowpass@1.4.0`). Each encoding has 37
files: 36 data files and a logFile. Counts below refer to this run.

---

## 1. What a PSF file contains

Regardless of encoding, a file holds three things:

| | |
|---|---|
| **Header** | Flat `str -> str \| int \| float` metadata. No nesting. |
| **Type catalogue** | Named types. Mostly a units dictionary: `V` is a float with `units=V`, `key=node`, `tolerance=1e-6`. Two constructors exist: `ARRAY` and `STRUCT`. |
| **Values** | Either a table of equal-length columns, or a set of independently typed named values. |

The catalogue is largely unused: `mysweep_ac1.sweep` declares 13 types and references exactly
one. Spectre writes its standard set of physical quantities whatever the file contains.

### 1.1 The four file shapes

Only `HEADER` and `END` are always present.

| shape | TYPE | SWEEP | TRACE | VALUE | files | example |
|---|:--:|:--:|:--:|:--:|--:|---|
| **A** header only | – | – | – | – | 1 | `myinfo_Models.info` |
| **B** named values | yes | – | – | yes | 4 | `myop.dc`, `logFile` |
| **C** sweep, no traces | yes | yes | – | yes | 8 | `mysweep_ac1.sweep` |
| **D** full table | yes | yes | yes | yes | 24 | `myac.ac`, `mytran.tran.tran` |

**Shape A is complete, not truncated.** `myinfo_Models` ran against a circuit with no models and
produced a header and nothing else.

**C and D are the same mechanism** at different widths: a table written row by row, each value
labelled with its column. Every column has the same length. `mytran` has 653 values in each of
`time`, `in`, `out` and `Vin:p`.

**B is different in kind.** Each entry carries its own type and its own annotations, so its
variables are declared inside the value section:

```
VALUE
"in" "V" 1              <- name, type reference, value
"out" "V" 1
```

In C and D the type comes from the declaration, and only the value appears:

```
VALUE
"freq" 1                <- name, value
"in" (1 0)
```

---

## 2. psfascii

Sections appear in the order `HEADER TYPE SWEEP TRACE VALUE END`, each introduced by a bare
uppercase keyword on its own line. Strings are double-quoted. `PROP( ... )` blocks carry key/value
annotations and may follow a type, a declaration or a value.

```
"V" FLOAT DOUBLE PROP( "units" "V" "key" "node" "tolerance" 1e-06 )
"sweepVariable" ARRAY ( * ) STRING *
"resistor" STRUCT( "trise" FLOAT DOUBLE ... ) PROP( "key" "inst" )
```

The `*` after a scalar type and inside `ARRAY ( * )` appears to be a placeholder (inferred).
Treating it as whitespace loses nothing.

Values dominate the size of a large file: 97% of the bytes in the ascii `mytran` come after
`VALUE`.

### 2.1 Floats may arrive without a decimal point

psfascii formats doubles with the simulator's `precision` option, which defaults to `"%g"`, six
significant digits. Formats in the `%g` family drop the decimal point for integral values, so
`1.0` is written `1` and tokenizes as an integer while the declared type is `FLOAT DOUBLE`.

`precision="%.17g"` round-trips float64 exactly, and the test corpus uses it. At the default of six
digits the text cannot represent the value the binary holds (`0.24` versus
`0.24000000000000002`), so the two encodings can only be compared to a tolerance.

---

## 3. psfbin

All integers are big-endian. Strings are a `uint32` length followed by that many bytes, padded with
zeros to a four-byte boundary.

### 3.1 File skeleton

```
offset 0     uint32   value-section layout (see 3.5)
offset 4     CONTAINER, header properties
             SECTION_TYPE  + CONTAINER ...
             SECTION_SWEEP + CONTAINER ...
             SECTION_TRACE + CONTAINER ...
             SECTION_VALUE + CONTAINER ...
             SECTION_END
             table of contents          (see 3.7)
             "Clarissa"                 8 bytes
             uint32                     offset of the table of contents
```

**The header section is not tagged.** Every other section is introduced by its `SECTION_*` chunk id,
but the file opens with the layout word and goes straight into a `CONTAINER`. `SECTION_HEADER` only
appears as a key in the table of contents.

`SECTION_HEADER` and the `NONE` layout share the value `0`, so the first word of a header-only file
is `0` for the layout reason, not the section reason.

The `Clarissa` magic near the end of the file also shows that the file was written to completion.

### 3.2 Chunk ids

```
 0 SECTION_HEADER    (table of contents only)   16 DECLARATION
 1 SECTION_TYPE                                 17 GROUP_DECLARATION
 2 SECTION_SWEEP                                18 STRUCT_END
 3 SECTION_TRACE                                19 CONTAINER_INDEX
 4 SECTION_VALUE                                20 CONTAINER_PADDING
15 SECTION_END                                  21 CONTAINER
                                                22 SUBCONTAINER
                                                33 PROP_STRING
                                                34 PROP_INT
                                                35 PROP_FLOAT
```

### 3.3 Containers: the size field is an absolute offset

A container is `CONTAINER, uint32, <contents>`. The `uint32` is not a length. It is an absolute file
offset:

- **`SUBCONTAINER`:** the offset at which its contents end.
- **`CONTAINER`:** the offset at which the next container begins, which is four bytes past the next
  section's tag. Its own contents therefore end at `value - 4`.

On `myop.dc`, the header container's field is `1016`, `SECTION_TYPE` sits at `1012` and the next
`CONTAINER` at `1016`. So every section carries a forward pointer, and a reader can skip a section
without parsing it.

### 3.4 Types

```
DECLARATION  uint32 id  string name  uint32 element_kind  uint32 kind  [members] [props]
```

`element_kind` is read unconditionally and is `0` for anything that is not an array. `0` is therefore
not a type. It means "no element type".

```
 1 INT8      signed byte
 2 STRING
 3 ARRAY
 5 INT32
11 FLOAT64
12 COMPLEX   two float64, real then imaginary
16 STRUCT    members follow until STRUCT_END (18)
```

Codes 4, 6-10 and 13-15 have never been observed. `STRING` and `ARRAY` have never been observed in
psfbin, only in psfascii, so reading them from psfbin is untested. `INT8` and `INT32` appear only as
struct members.

**`INT8` occupies a four-byte big-endian slot and is signed.** The value is in the last byte. Reading
the first byte returns `0` for the value `1`. A value of `-1` hides this, since `0xFFFFFFFF` reads as
`0xFF` from any offset.

### 3.5 Value section layouts

The file's first word declares how the value section is laid out:

| value | name | meaning | files |
|---:|---|---|--:|
| 0 | `NONE` | no values at all (shape A) | 1 |
| 512 | `TAGGED` | a table, one value at a time, each tagged with its declaration id | 28 |
| 1024 | `WINDOWED` | a table, in blocks of contiguous per-column runs | 4 |
| 1280 | `ENTRIES` | independently typed named values (shape B) | 3 |

**`TAGGED`** is a repeating row:

```
DECLARATION  uint32 column_id  value     once per column, in the same order every row
```

Rows have a fixed size in all 28 files, whose columns are all `FLOAT64` or `COMPLEX`. So the rows can
be read as one array, and the column ids checked against the declarations as they go by. A variable-size
value such as a string would break this, and has never been observed in a table.

### 3.6 The windowed layout

Used for transients. Measured on `mytran.tran.tran` (653 points, 4 columns):

```
CONTAINER_PADDING pads the section so the first block starts at PSF window size (4096)

each block:
  DECLARATION  uint16 window  uint16 count
  then per column:
      count   x float64          the data
      (window - count) x float64 unused slots
      float64 0xFFFFFFFF7FFFFFFF a NaN sentinel, between columns only
```

`window` is how many values a column can hold in a block, and `count` is how many it does. Blocks are
`PSF buffer size` (16384) bytes apart, and `window` follows from that:

```
(16384 - 8 header - 3 separators x 8) / 4 columns / 8 bytes = 511
```

Observed blocks: `window=511 count=511` then `window=511 count=142`, and 511 + 142 = 653, matching
`PSF sweep points`. The Monte Carlo transients have one block, `window=511 count=62`.

`CONTAINER_PADDING` may appear before any block, not only the first. Each column's values sit at a
computable offset within a block, so one column can be read without touching the others.

All observed windowed columns are `FLOAT64`. Whether another type can occur here is unknown.

### 3.7 Table of contents

Immediately before the `"Clarissa"` magic, the file carries pairs of `uint32 section_id, uint32
container_offset`:

```
myop.dc              HEADER@4  TYPE@1016  VALUE@2360
mysweep_ac1.sweep    HEADER@4  TYPE@908   SWEEP@2256  VALUE@2372
myac.ac              HEADER@4  TYPE@956   SWEEP@2304  TRACE@2420  VALUE@2560
myinfo_Models.info   HEADER@4
```

Every offset lands exactly on a `CONTAINER` chunk, in all 36 binary data files. A reader can therefore
seek directly to any section. For `mytran.tran.tran` the table reads `{HEADER: 4, TYPE: 1552, SWEEP:
2956, TRACE: 3072, VALUE: 3252}` in a 36924-byte file, so the declarations end at 3252, with the
33 KB of values behind them.

A `SECTION_END` word precedes the table. In windowed files a second `SECTION_END` appears at the start
of the table itself, so a reader should skip leading `SECTION_END` words until the remaining length is
a multiple of eight.

### 3.8 Container indexes

`TYPE` and `TRACE` containers, and `VALUE` containers in the `ENTRIES` layout, end with a
`CONTAINER_INDEX`: a chunk id, a `uint32` byte length, then fixed-size entries. Entries are stored in
an order that is neither declaration order nor sorted.

**TYPE**, 8-byte entries: `uint32 declaration_id, uint32 n`, where `n` is always `declaration_id` minus
a per-file base. Derived data.

**TRACE**, 16-byte entries, one per trace and one per group:

```
6f75 7400  0000 000c  0000 0130  ffff ffff     "out\0"  12   304   -1
696e 0000  0000 000b  0000 0130  ffff ffff     "in\0\0"  11   304   -1
6772 6f75  0000 000a  0000 0000  0000 0003     "grou"   10     0    3
5669 6e3a  0000 000d  0000 0130  ffff ffff     "Vin:"   13   304   -1
```

The first four bytes are the first four characters of the name, truncated (`Vin:p` becomes `Vin:`), not
an identifier. Then a per-file sequence number. The third word is `0` in `TAGGED` files and `0x130` in
windowed ones, and its meaning is unknown. The fourth is `-1` for a plain trace and, for a group, its
member count.

**VALUE**, 8-byte entries, one per entry. Known from the sizes alone. The contents have not been decoded.

Nothing in any index is needed to parse the file. Each can be skipped by its byte length.

### 3.9 Group declarations

psfbin wraps the traces of a windowed transient in a `GROUP_DECLARATION`:

```
GROUP_DECLARATION  uint32 id  string name  uint32 member_count  <member declarations>
```

In every file observed the group is flat, one group named `group` holding the traces. It carries no
meaning beyond packaging, so its members can be treated as ordinary traces. `PSF groups` in the header
says how many exist.

Genuinely nested groups have never been observed, and no psfascii file contains a group at all, so the
ascii spelling of one is unknown.

### 3.10 The header describes the file

psfbin adds header keys that psfascii does not, and several state the file's own shape. From `mytran`:

```
PSF types          14        number of type declarations
PSF sweeps          1        number of sweeps
PSF sweep points  653        rows in the table
PSF sweep min/max            range of the sweep variable
PSF traces          3        number of traces
PSF groups          1        number of group declarations
PSF window size  4096        windowed only: offset the first block starts at
PSF buffer size 16384        windowed only: bytes between blocks
PSF style           7        unknown
```

`PSF sweep points` equals the row count in all 32 swept binary files, so it is an independent check on
the value section. The other added keys are `BINPSF creation time`, `PSF_LIB_BUILD_VER` and `ENV_VAR_n`.

---

## 4. The logFile

A raw folder holds one file per analysis, plus a `logFile`. The logFile is an ordinary shape-B PSF file
and always psfascii, whatever `-format` the run used. Each entry is a struct describing one other file:

```
"mysweep-001_mynestedsweep-002_ac2-ac" "analysisInst" (
"ac"                                                         analysisType
"mysweep-001_mynestedsweep-002_ac2.ac"                       dataFile
"PSF"                                                        format
"mysweep-001_mynestedsweep_ac2-sweep"                        parent
("freq")                                                     sweepVariable
"AC Analysis `...': freq = (1 Hz -> 1 MHz)"                  description
) PROP( "data_type" "swept_scalar" "sweep_tree_type" "leafNode" "C1:c" 3e-06 )
```

### 4.1 The sweep tree

The `parent` field links entries into a forest. An empty `parent` marks a root: 12 of the 36 entries.

| `sweep_tree_type` | entries | meaning |
|---|--:|---|
| `sweepNode` | 6 | a sweep with children |
| `leafNode` | 21 | a file holding data, under a sweep |
| absent | 9 | 7 standalone analyses, and 2 Monte Carlo roots |

**The tree comes from `parent`, not from `sweep_tree_type`.** The Monte Carlo root `mymonte_dc2-montecarlo`
has children but no `sweep_tree_type`.

### 4.2 Each node holds only its own coordinate

A sweep's value at a child appears on that child, as a property named after the swept parameter. So a
full set of coordinates is collected by walking up through the parents:

```
mysweep_ac2-sweep                        (root)         sweepVariable R1:r
mysweep-001_mynestedsweep_ac2-sweep      R1:r = 2000    sweepVariable C1:c
mysweep-001_mynestedsweep-002_ac2-ac     C1:c = 3e-06   sweepVariable freq
```

The outer coordinates appear only here, never in the data file. So the quantity `out` in this nested sweep,
`out[R1:r, C1:c, freq]` with shape (3, 3, 61), is spread over 9 files, and only the logFile can put it
back together.

A Monte Carlo run has the same structure, with `iteration` as the swept parameter.

`sweepVariable` is an array, but it holds at most one name in this corpus.

---

## 5. The two encodings disagree about their own version

The same simulation reports different `PSFversion` in each format: `1.00` in psfascii and `1.1` in psfbin.
`PSFversion` is therefore no use as a discriminator. The `psfversion` reported in the `logFile` (`1.4.0`) is
the format version worth tracking. It is a different key from `PSFversion`. Cadence's documented `psfversion`
option is described as psfxl-specific, yet the key reports `1.4.0` for a psfbin run.

---

## 6. Known unknowns

- Whether `PROP_INT` and `INT32` are signed. No value in the corpus has the high bit set, so the two readings
  cannot be told apart. `INT8` turned out to be signed.
- What `PSF style = 7` means.
- What `0x130` means in a windowed trace index entry.
- Datatype codes 4, 6-10 and 13-15.
- psfbin files containing `STRING` or `ARRAY` values.
- Windowed columns of any type other than `FLOAT64`.
- psfascii group declarations, and nested groups in either encoding.
- `sweepVariable` with more than one name.
- psfxl. It is Spectre's default (`rawfmt=psfxl`) and is not supported, so runs must pass `-format`.

---

## 7. How to check a claim about the format

Generate the same simulation in both encodings and compare the parsed results (`tests/test_load.py`). psfascii
is textual and can be read by eye, and psfbin cannot, so every file present in both is a free check on the
binary reader.

That method found the bugs described in 2.1 and 3.4. It proves only that the two readers agree. To know they are
right, compare against a value you can derive independently, such as the -3 dB point of a known RC network.
