from psf_parser.binary.parser import PsfBinParser


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


def test_binary_oppoint(psf_test_files):
    file = psf_test_files / "binary/myop.dc"
    parser = PsfBinParser(file).parse()
    expect(parser, 13, 0, 0, 2)


def test_binary_dc(psf_test_files):
    file = psf_test_files / "binary/mydc.dc"
    parser = PsfBinParser(file).parse()
    expect(parser, 14, 1, 2, 0)


def test_binary_ac(psf_test_files):
    file = psf_test_files / "binary/myac.ac"
    parser = PsfBinParser(file).parse()
    expect(parser, 13, 1, 2, 0)


def test_binary_tran(psf_test_files):
    file = psf_test_files / "binary/mytran.tran.tran"
    parser = PsfBinParser(file).parse()
    expect(parser, 14, 1, 2, 0)


def test_binary_nested_tran(psf_test_files):
    file = psf_test_files / "binary/tran1.tran.tran"
    parser = PsfBinParser(file).parse()
    expect(parser, 14, 1, 2, 0)


def test_binary_monte(psf_test_files):
    file = psf_test_files / "binary/mymonte_dc2.montecarlo"
    parser = PsfBinParser(file).parse()
    expect(parser, 13, 1, 0, 0)


def test_binary_info_all(psf_test_files):
    file = psf_test_files / "binary/myinfo_all.info"
    parser = PsfBinParser(file).parse()
    expect(parser, 202, 0, 0, 5)


def test_binary_info_models(psf_test_files):
    file = psf_test_files / "binary/myinfo_Models.info"
    parser = PsfBinParser(file).parse()
    expect(parser, 0, 0, 0, 0)


def test_binary_info_oppoint(psf_test_files):
    file = psf_test_files / "binary/myinfo_Oppoint.info"
    parser = PsfBinParser(file).parse()
    expect(parser, 13, 0, 0, 3)


def test_binary_spectre_lx_10signals(psf_test_files):
    file = psf_test_files / "binary/spectre-lx-10signals.sweep"
    parser = PsfBinParser(file).parse()
    expect(parser, 15, 1, 10, 0)
