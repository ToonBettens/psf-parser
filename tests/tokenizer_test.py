from pathlib import Path
from psf_parser.ascii.token import Tokenizer

tests_dir = Path.cwd() / "tests"
path = (tests_dir / "data/sweep/vgs-005_vds.dc")

text = path.read_text()

tokenizer = Tokenizer(text)
while tokenizer.has_next():
    token = tokenizer.next()
    print(token)
