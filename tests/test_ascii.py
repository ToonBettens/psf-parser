from psf_parser.ascii.parser import PsfAsciiParser


def expect(
    parser,
    num_types = 0,
    num_sweeps = 0,
    num_traces = 0,
    num_values = 0,
):
    assert len(parser.registry.types) == num_types
    assert len(parser.registry.sweeps) == num_sweeps
    assert len(parser.registry.traces) == num_traces
    assert len(parser.registry.values) == num_values


def test_ascii_oppoint(psf_test_files):
    file = psf_test_files / "ascii/myop.dc"
    parser = PsfAsciiParser(file).parse()
    expect(parser, 13, 0, 0, 2)


def test_ascii_dc(psf_test_files):
    file = psf_test_files / "ascii/mydc.dc"
    parser = PsfAsciiParser(file).parse()
    expect(parser, 14, 1, 2, 0)


def test_ascii_ac(psf_test_files):
    file = psf_test_files / "ascii/myac.ac"
    parser = PsfAsciiParser(file).parse()
    expect(parser, 13, 1, 2, 0)


def test_ascii_tran(psf_test_files):
    file = psf_test_files / "ascii/mytran.tran.tran"
    parser = PsfAsciiParser(file).parse()
    expect(parser, 14, 1, 2, 0)


def test_ascii_nested_tran(psf_test_files):
    file = psf_test_files / "ascii/tran1.tran.tran"
    parser = PsfAsciiParser(file).parse()
    expect(parser, 14, 1, 2, 0)


def test_ascii_monte(psf_test_files):
    file = psf_test_files / "ascii/mymonte_dc2.montecarlo"
    parser = PsfAsciiParser(file).parse()
    expect(parser, 13, 1, 0, 0)


def test_ascii_info_all(psf_test_files):
    file = psf_test_files / "ascii/myinfo_all.info"
    parser = PsfAsciiParser(file).parse()
    expect(parser, 202, 0, 0, 5)


def test_ascii_info_models(psf_test_files):
    file = psf_test_files / "ascii/myinfo_Models.info"
    parser = PsfAsciiParser(file).parse()
    expect(parser, 0, 0, 0, 0)


def test_ascii_info_oppoint(psf_test_files):
    file = psf_test_files / "ascii/myinfo_Oppoint.info"
    parser = PsfAsciiParser(file).parse()
    expect(parser, 13, 0, 0, 3)
