# Test netlists

The Spectre netlists that the runs in `tests/data/runs/` come from. Each one is simulated
twice, once with `-format psfascii` and once with `-format psfbin`, and its run is named
`<netlist>@<Spectre version>`. The netlists use only built-in components and hand-written
model cards, so they run without a PDK.

| Group | Needs | Holds |
| --- | --- | --- |
| `base` | Spectre | Everything plain Spectre can run |
| `rf` | SpectreRF | Periodic and quasi-periodic analyses |
| `large` | Spectre | One big file to measure speed on, not committed |
| `probes` | Spectre | One-off experiments on what changes the files, not committed |

Each group needs one licence, so leaving out a group is enough to run the others without it.
