from pathlib import Path
from psf_parser.binary.parser import PsfBinParser

data_dir = Path.cwd() / "tests/data/binary/"

parser = PsfBinParser(data_dir / "myop.dc").parse()
assert len(parser.registry.sweeps) == 0
assert len(parser.registry.traces) == 0
assert len(parser.registry.values) == 2

parser = PsfBinParser(data_dir / "mydc.dc").parse()
assert len(parser.registry.sweeps) == 1
assert len(parser.registry.traces) == 2
assert len(parser.registry.values) == 0

parser = PsfBinParser(data_dir / "myac.ac").parse()
assert len(parser.registry.sweeps) == 1
assert len(parser.registry.traces) == 2
assert len(parser.registry.values) == 0

parser = PsfBinParser(data_dir / "mytran.tran.tran").parse()
assert len(parser.registry.sweeps) == 1
assert len(parser.registry.traces) == 2
assert len(parser.registry.values) == 0

parser = PsfBinParser(data_dir / "tran1.tran.tran").parse()
assert len(parser.registry.sweeps) == 1
assert len(parser.registry.traces) == 2
assert len(parser.registry.values) == 0

parser = PsfBinParser(data_dir / "mysweep_ac1.sweep").parse()
assert len(parser.registry.sweeps) == 1
assert len(parser.registry.traces) == 0
assert len(parser.registry.values) == 0

parser = PsfBinParser(data_dir / "mymonte_dc2.montecarlo").parse()
assert len(parser.registry.sweeps) == 1
assert len(parser.registry.traces) == 0
assert len(parser.registry.values) == 0

parser = PsfBinParser(data_dir / "myinfo_all.info").parse()
assert len(parser.registry.sweeps) == 0
assert len(parser.registry.traces) == 0
assert len(parser.registry.values) == 5

parser = PsfBinParser(data_dir / "myinfo_Models.info").parse()
assert len(parser.registry.sweeps) == 0
assert len(parser.registry.traces) == 0
assert len(parser.registry.values) == 0

parser = PsfBinParser(data_dir / "myinfo_Oppoint.info").parse()
assert len(parser.registry.sweeps) == 0
assert len(parser.registry.traces) == 0
assert len(parser.registry.values) == 3
