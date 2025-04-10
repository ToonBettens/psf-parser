from pathlib import Path
from psf_parser.sim import Simulation

tests_dir = Path.cwd() / "tests"
path = (tests_dir / "data/sweep/")

sim = Simulation.from_raw("somename", path)
print(dir(sim))

print()

print(dir(sim.analyses['vgs_vds.sweep']))
