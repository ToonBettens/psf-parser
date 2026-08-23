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

# We can scan the spectre version from the logFile
VERSION_RE = re.compile(r'"version"\s+"([^"]+)"')


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


def read_version(raw_dir):
    """Extract the simulator version from the run's logFile."""
    log_path = os.path.join(raw_dir, "logFile")
    if not os.path.isfile(log_path):
        return "unknown"
    with open(log_path) as handle:
        match = VERSION_RE.search(handle.read())
    return match.group(1) if match else "unknown"


def short_version(version):
    """23.1.0.242.isr1 -> 23.1 — enough to distinguish runs, short enough to read."""
    parts = version.split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else version


def write_run_toml(path, netlist, version, formats, command):
    lines = [
        f'netlist  = "{os.path.basename(netlist)}"',
        f'spectre  = "{version}"',
        f'command  = "{command}"',
        "formats  = [{}]".format(", ".join(f'"{f}"' for f in formats)),
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

    stem = os.path.basename(args.netlist).split(".")[0]
    staging = tempfile.mkdtemp(prefix="psf-generate-")
    produced = {}

    try:
        for fmt in formats:
            print(f"[{fmt}]")
            produced[fmt] = run_spectre(args.spectre, args.netlist, fmt, os.path.join(staging, FORMATS[fmt]))

        version = read_version(next(iter(produced.values())))
        run_name = f"{stem}@{short_version(version)}"
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
            version,
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
        print(f"Spectre version: {version}")
        print(f"Next: copy {run_name} into tests/data/runs/")
    finally:
        shutil.rmtree(staging, ignore_errors=True)


if __name__ == "__main__":
    main()
