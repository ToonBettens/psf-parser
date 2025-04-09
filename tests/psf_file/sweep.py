from pathlib import Path
from psf_parser.psf_file import PSFFile

tests_dir = Path.cwd() / "tests"
path = (tests_dir / "data/bin/vgs-001_vds.dc")

psf_file = PSFFile(path)
print(psf_file.signals.keys())
print(psf_file.sweeps.keys())
