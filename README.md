# psf-parser

A pure-Python parser for Cadence's proprietary PSF format. Supports both ASCII and binary variants. No external dependencies.

## Features

- ✅ Parses both ASCII and binary PSF files
- ✅ No dependencies (standard library only)
- ✅ Provides structured access to signals, traces, sweeps, and values

## Installation

To install the `psf-parser` package, simply run:

```
pip install psf_parser
```

## Usage

The `psf-parser` package provides a straightforward API for parsing and accessing the contents of PSF files. It supports both ASCII and binary formats.

### Example Usage

Here’s an example of how to use the `PsfFile` classes to access PSF file content.

```python
from psf_parser import PsfFile

file = PsfParser("path/to/psf")
print(file.sweeps)
print(file.traces)
print(file.values)
```

## License

This project is licensed under the MIT License – see the [LICENSE](./LICENSE) file for details.

## Acknowledgements

This project was made possible thanks to the inspiration and information provided by the following projects:

- [`psf_utils`](https://github.com/kenkundert/psf_utils) – A well-established PSF parser built with PLY, helpful for understanding the PSF ASCII format.
- [`libpsf`](https://github.com/henjo/libpsf) – The original reverse-engineering project for the binary PSF format, which served as the primary source for this implementation.

Special thanks to the maintainers and contributors of these projects for their open source work.
