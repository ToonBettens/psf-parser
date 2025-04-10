from pathlib import Path
from psf_parser.parser import PsfParser
from psf_parser.file import PsfFile

tests_dir = Path.cwd() / "tests"
path = (tests_dir / "data/sweep/vgs_vds.sweep")

# parser = PsfParser(path)
# parser.parse()
# parser.print_timing_report()

file = PsfFile(path)
print(file.sweeps.keys())
print(file.traces.keys())
print(file.values.keys())

print()

path = (tests_dir / "data/sweep/logFile")
file = PsfFile(path)
print(file.sweeps.keys())
print(file.traces.keys())
print(file.values.keys())

file.parser.print_timing_report()
