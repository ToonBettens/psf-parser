from pathlib import Path
from psf_parser import PsfFile

data_dir = Path.cwd() / "tests/data/bin/"

file = PsfFile(data_dir / "logFile")
assert len(file.sweeps) == 0
assert len(file.traces) == 0
assert len(file.values) == 38

file = PsfFile(data_dir / "myop.dc")
assert len(file.sweeps) == 0
assert len(file.traces) == 0
assert len(file.values) == 2

file = PsfFile(data_dir / "mydc.dc")
assert len(file.sweeps) == 1
assert len(file.traces) == 2
assert len(file.values) == 0

file = PsfFile(data_dir / "myac.ac")
assert len(file.sweeps) == 1
assert len(file.traces) == 2
assert len(file.values) == 0

file = PsfFile(data_dir / "mytran.tran.tran")
assert len(file.sweeps) == 1
assert len(file.traces) == 2
assert len(file.values) == 0

file = PsfFile(data_dir / "tran1.tran.tran")
assert len(file.sweeps) == 1
assert len(file.traces) == 2
assert len(file.values) == 0

file = PsfFile(data_dir / "mysweep_ac1.sweep")
assert len(file.sweeps) == 1
assert len(file.traces) == 0
assert len(file.values) == 0

file = PsfFile(data_dir / "mymonte_dc2.montecarlo")
assert len(file.sweeps) == 1
assert len(file.traces) == 0
assert len(file.values) == 0

file = PsfFile(data_dir / "myinfo_all.info")
assert len(file.sweeps) == 0
assert len(file.traces) == 0
assert len(file.values) == 5

file = PsfFile(data_dir / "myinfo_Models.info")
assert len(file.sweeps) == 0
assert len(file.traces) == 0
assert len(file.values) == 0

file = PsfFile(data_dir / "myinfo_Oppoint.info")
assert len(file.sweeps) == 0
assert len(file.traces) == 0
assert len(file.values) == 3
