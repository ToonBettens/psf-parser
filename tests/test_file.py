from psf_parser import PsfFile, PsfParser

def test_psf_file(psf_test_files):
    file = psf_test_files / "binary/mydc.dc"
    parser = PsfParser(file).parse()
    psf = PsfFile(file)

    assert psf.header == parser.header
    assert len(psf.sweeps) == len(parser.registry.sweeps)
    assert len(psf.traces) == len(parser.registry.traces)
    assert len(psf.values) == len(parser.registry.values)
    assert len(psf.signals) == len(parser.registry.sweeps) + len(parser.registry.traces) + len(parser.registry.values)
