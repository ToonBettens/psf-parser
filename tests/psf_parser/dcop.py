from pathlib import Path
from psf_parser.parser import PsfParser

tests_dir = Path.cwd() / "tests"
path = (tests_dir / "data/bin/dcOp.dc")

parser = PsfParser(path).parse()
print(parser.registry)
