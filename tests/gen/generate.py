#!/usr/bin/env python3
"""Generate psf-parser test data by running Spectre on a netlist."""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

# Spectre's -format value
FORMATS = {
    "psfascii": "ascii",
    "psfbin": "binary",
}

# The PSF format version, from the run's logFile (always psfascii, whatever
# -format was requested, so it reads without parsing any binary). This is the
# axis the parser needs coverage across. The simulator version is not tracked
# separately -- every generated file carries it in its own header already.
PSFVERSION_RE = re.compile(r'"psfversion"\s+"([^"]+)"')

# Anything outside this set is replaced when building a directory name.
UNSAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")


def run_spectre(spectre, netlist, fmt, outdir):
    """Run Spectre once, writing a raw directory in the requested format."""
    cmd = [spectre, netlist, "-format", fmt, "-raw", outdir]
    print("  $ " + " ".join(cmd))
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise SystemExit(f"could not run {spectre!r}: {exc}") from exc
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        raise SystemExit(f"spectre failed for -format {fmt} (exit {result.returncode})")
    if not os.path.isdir(outdir):
        raise SystemExit(f"spectre produced no raw directory at {outdir}")
    return outdir


def read_psfversion(raw_dir):
    """Read the PSF format version from the run's logFile."""
    log_path = os.path.join(raw_dir, "logFile")
    if not os.path.isfile(log_path):
        return "unknown"
    with open(log_path) as handle:
        match = PSFVERSION_RE.search(handle.read())
    return match.group(1) if match else "unknown"


def safe_name(text):
    """Make `text` safe to use unquoted in a directory name."""
    return UNSAFE_RE.sub("-", text.strip()).strip("-.") or "unknown"


def write_run_toml(path, netlist, psfversion, formats, command):
    lines = [
        f'netlist    = "{os.path.basename(netlist)}"',
        f'psfversion = "{psfversion}"',
        f'command    = "{command}"',
        "formats    = [{}]".format(", ".join(f'"{f}"' for f in formats)),
    ]
    with open(path, "w") as handle:
        handle.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("netlist", help="Spectre netlist to simulate")
    parser.add_argument("--outdir", default="runs", help="where to write the run directory (default: ./runs)")
    parser.add_argument("--spectre", default="spectre", help="spectre executable (default: spectre on PATH)")
    parser.add_argument(
        "--formats",
        default="psfascii,psfbin",
        help="comma-separated Spectre output formats (default: psfascii,psfbin)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.netlist):
        raise SystemExit(f"no such netlist: {args.netlist}")

    formats = [f.strip() for f in args.formats.split(",") if f.strip()]
    for fmt in formats:
        if fmt not in FORMATS:
            raise SystemExit("unsupported format {!r}; choose from {}".format(fmt, ", ".join(sorted(FORMATS))))

    if os.path.dirname(args.spectre):
        if not os.path.isfile(args.spectre):
            raise SystemExit(f"no such spectre executable: {args.spectre}")
    elif shutil.which(args.spectre) is None:
        raise SystemExit(
            f"{args.spectre!r} is not on PATH.\n"
            "If Spectre is behind a module system, load it first "
            "(e.g. `module load spectre`) or pass --spectre /path/to/spectre."
        )

    stem = safe_name(os.path.basename(args.netlist).split(".")[0])
    staging = tempfile.mkdtemp(prefix="psf-generate-")
    produced = {}

    try:
        for fmt in formats:
            print(f"[{fmt}]")
            produced[fmt] = run_spectre(args.spectre, args.netlist, fmt, os.path.join(staging, FORMATS[fmt]))

        psfversion = read_psfversion(next(iter(produced.values())))
        # Named after psfversion, not the simulator: the parser needs coverage
        # across PSF format versions, and two Spectre releases writing the same
        # psfversion produce structurally identical files.
        run_name = f"{stem}@{safe_name(psfversion)}"
        run_dir = os.path.join(args.outdir, run_name)

        if os.path.exists(run_dir):
            raise SystemExit(f"{run_dir} already exists.\nRuns are never overwritten so that versions can coexist -- remove it first, or use --outdir.")

        raw_dir = os.path.join(run_dir, "raw")
        os.makedirs(raw_dir)
        for fmt in formats:
            shutil.copytree(produced[fmt], os.path.join(raw_dir, FORMATS[fmt]))

        write_run_toml(
            os.path.join(run_dir, "run.toml"),
            args.netlist,
            psfversion,
            [FORMATS[f] for f in formats],
            f"{os.path.basename(args.spectre)} {os.path.basename(args.netlist)} -format {{format}} -raw {{outdir}}",
        )

        print("")
        print(f"Wrote {run_dir}")
        for fmt in formats:
            target = os.path.join(raw_dir, FORMATS[fmt])
            count = len(os.listdir(target))
            has_log = "logFile" in os.listdir(target)
            print("  raw/{:<8} {:3d} files{}".format(FORMATS[fmt], count, "" if has_log else "  (no logFile!)"))
        print("")
        print(f"psfversion {psfversion}")
        print(f"Next: copy {run_name} into tests/data/runs/")
    finally:
        shutil.rmtree(staging, ignore_errors=True)


if __name__ == "__main__":
    main()
