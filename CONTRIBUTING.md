# Contributing to psf-parser

Bug reports, failing PSF files, and pull requests are all welcome.

## Why this project needs your files

Cadence has never published a specification for the PSF format. This parser is built
entirely by reverse-engineering simulator output and observing patterns, which means its
coverage is bounded by the variety of files it has been tested against.

It is currently verified against Spectre output from:

- Oppoint analyses
- DC sweeps
- AC simulations
- Transient simulations
- Monte Carlo
- Nested sweeps
- Various info analysis statements

If you have a PSF file that fails to parse or produces incorrect output, **that file is the
single most useful thing you can contribute.**

## Reporting a file that does not parse

Please open an issue including:

1. The analysis type (`tran`, `ac`, `dc`, `noise`, `pss`, ...)
2. The output format (`psfascii`, `psfbin`, `psfxl`)
3. The Spectre version that produced it
4. The file itself, or a reduced version of it, if you are able to share it

If the data is confidential, a minimal reproducer generated from a dummy circuit is just as
valuable — the circuit does not matter, only the file structure does.

## Development setup

This project uses [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/ToonBettens/psf-parser
cd psf-parser
uv sync
```

Then run the checks:

```bash
uv run pytest          # tests
uv run ruff check .    # lint
uv run ruff format .   # format
uv run ty check        # type check
```

The minimum supported Python is 3.11. `.python-version` pins local development to that
floor, so syntax that requires a newer interpreter fails on your machine rather than in
review.

## Docstrings and comments

Keep them short, factual and in the present tense. Say what the code does, without history,
first person or judgement. Reasoning and alternatives belong in `docs/design.md`.

- **Public names** get a docstring with full `Args:`, `Returns:` and `Raises:` sections. Each
  entry says more than the name does, including units and array shapes where relevant.
- **Private names**, anything under a leading underscore, get a one-line docstring when the
  name is not enough.
- **Comments** say why, not what. A fact about the format is one line pointing to its evidence:
  `# A signed byte in a four-byte big-endian slot (format-notes 3.4).`
- **The format has no specification**, so a claim about it says how we know it. "Observed"
  means seen in test files but not specified.
- **Tests** say what they check in their name. A docstring adds only what the name cannot.

## Pull requests

- Add a test alongside any parser change. New PSF files belong in `tests/data/`.
- Keep formatting-only changes in their own commit, separate from behavioural ones.
- Give the pull request a descriptive title — release notes are generated from them.
