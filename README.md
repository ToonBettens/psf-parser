# psf-parser

**psf-parser** is a lightweight, dependency-free Python parser for Cadence's proprietary **PSF (Parameter Storage Format)** files.
It supports both the ASCII (`psfascii`) and binary (`psfbin`) formats.

> **Note:**
> While Spectre uses psfbin as the default output format for most simulations, transient simulations typically use the psfxl format, which this parser does not support. To avoid issues, set the output format explicitly to psfbin.

---

## Installation

Install `psf-parser` directly via pip:

```bash
pip install psf-parser
```

---

## Usage

The `psf-parser` package provides a simple API for parsing and accessing PSF file contents.
It automatically detects the file format (ASCII or binary), but you can also specify it manually.

```python
from psf_parser import PsfFile

psf = PsfFile("path/to/psf")
print(psf.header)
print(psf.sweeps)
print(psf.traces)
print(psf.values)
```

If you prefer lower-level access to the raw registry data, you can work directly with the parser classes:

```python
from psf_parser import PsfParser

parser = PsfParser("path/to/ascii/psf", format="ascii").parse()
print(parser.header)
print(parser.registry.types)
```

**Notes:**
- `PsfParser` acts as a factory and dispatches to the correct format-specific parser.
- `PsfAsciiParser` and `PsfBinParser` handle the ASCII and binary formats respectively (for internal or advanced usage).

---

## License

This project is licensed under the [MIT License](./LICENSE).

---

## Acknowledgements

This project was made possible by the excellent prior work of:

- [`psf_utils`](https://github.com/kenkundert/psf_utils) — a psfascii parser built with PLY.
- [`libpsf`](https://github.com/henjo/libpsf) — the original reverse-engineering project for the binary PSF format.
