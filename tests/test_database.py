"""A raw folder opens as a Database: its analyses, their netlist paths, and what the logFile says about them."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from tests.conftest import RUNS_DIR

import psf_parser

# The path of every analysis in the corpus, in logFile order. A change to the naming rules shows here
# as a diff. Entry names stand in where no netlist path can be derived (format-notes 4.4).
EXPECTED_PATHS = {
    "default_precision@25.1": ["myop", "mydc", "myac", "mytran"],
    "device_match@25.1": [
        "myop",
        "myop.sens",
        "myac",
        "myac.sens",
        "mymatch",
        "mytemp_myswept-sweep",
        "mytemp-000_myswept-dcmatch",
        "mytemp-001_myswept-dcmatch",
        "mytemp-002_myswept-dcmatch",
    ],
    "long_tran@21.1": ["mytran"],
    "long_tran@25.1": ["mytran"],
    "rc_lowpass@23.1": [
        "myinfo_Oppoint",
        "myinfo_Models",
        "myinfo_all",
        "myop",
        "mydc",
        "myac",
        "mytran",
        "mysweep/dc1",
        "mysweep/ac1",
        "mysweep/mynestedsweep/ac2",
        "mymonte/dc2",
        "mymonte/tran1",
    ],
    "rf_periodic@25.1": [
        "mypss.td",
        "mypss.fd",
        "mypac",
        "mypxf",
        "mypnoise",
        "mypsp",
        "mypstb",
        "mypstb.margin",
        "mysweep/pss2.td",
        "mysweep/pss2.fd",
        "mysweep/pac2",
    ],
    "rf_quasi@25.1": [
        "myqpss.fi",
        "myqpss.fd",
        "myqpac",
        "myqpnoise",
        "myhb.fd",
        "myhb.fi",
        "myhbac",
        "myenv.fd",
        "myenv.td",
    ],
    "small_signal@25.1": [
        "mynoise",
        "myxf",
        "mypz",
        "mysp",
        "myspnoise.noise",
        "myspnoise",
        "mystb",
        "mystb.margin",
    ],
    "sweeps@25.1": ["mypairs/ac1", "mytemp/dc1", "mytemp/tr1", "mymonte/myinner/dc2", "before", "after"],
    "types@25.1": ["pars", "allp.info", "insts", "subs.info", "prims.info", "every", "myop"],
}
# Spectre 21.1 and 23.1 name their entries as 25.1 does.
EXPECTED_PATHS["rc_lowpass@25.1"] = EXPECTED_PATHS["rc_lowpass@23.1"]
for _name in ("long_tran", "rf_quasi", "sweeps", "types"):
    EXPECTED_PATHS[f"{_name}@21.1"] = EXPECTED_PATHS[f"{_name}@25.1"]


def _folders() -> list[Path]:
    return sorted(folder for run in RUNS_DIR.iterdir() for folder in run.iterdir() if folder.is_dir())


def _copy(tmp_path: Path, run: str, fmt: str = "ascii") -> Path:
    return Path(shutil.copytree(RUNS_DIR / run / fmt, tmp_path / run))


def _edit_logfile(folder: Path, old: str, new: str, count: int = -1) -> None:
    logfile = folder / "logFile"
    text = logfile.read_text()
    assert old in text
    logfile.write_text(text.replace(old, new, count))


def test_every_run_has_expected_paths():
    assert sorted(EXPECTED_PATHS) == sorted(run.name for run in RUNS_DIR.iterdir() if run.is_dir())


@pytest.mark.parametrize("folder", _folders(), ids=lambda folder: f"{folder.parent.name}/{folder.name}")
def test_paths_of_every_analysis(folder):
    db = psf_parser.Database(folder)
    assert list(db.analyses) == EXPECTED_PATHS[folder.parent.name]
    for path, analysis in db.analyses.items():
        assert analysis.path == path
        assert analysis.has_path == (path != analysis.entry)
        assert db[path] is analysis
        assert db.entry(analysis.entry) is analysis
        assert analysis.missing == ()


def test_unlinked_dcmatch_keeps_entry_names():
    db = psf_parser.Database(RUNS_DIR / "device_match@25.1" / "ascii")
    unlinked = db["mytemp-000_myswept-dcmatch"]
    assert not unlinked.has_path
    assert unlinked.entry == "mytemp-000_myswept-dcmatch"


def test_nested_sweep_names_its_root_and_levels():
    db = psf_parser.Database(RUNS_DIR / "rc_lowpass@25.1" / "binary")
    analysis = db["mysweep/mynestedsweep/ac2"]
    assert analysis.entry == "mysweep_ac2-sweep"
    assert [level.name for level in analysis._levels] == ["R1:r", "C1:c"]
    assert [level.counts for level in analysis._levels] == [(3,), (3, 3, 3)]


def test_paramset_level_is_named_after_its_statement():
    db = psf_parser.Database(RUNS_DIR / "sweeps@21.1" / "ascii")
    (level,) = db["mypairs/ac1"]._levels
    assert level.name == "mypairs"
    assert level.parameters == ("rval", "cval")


def test_listing_shows_paths_and_axes():
    listing = str(psf_parser.Database(RUNS_DIR / "rc_lowpass@25.1" / "ascii")).splitlines()
    assert listing[0].endswith("rc_lowpass@25.1/ascii: 12 analyses")
    assert listing[10].split() == ["mysweep/mynestedsweep/ac2", "R1:r", "(3),", "C1:c", "(3),", "freq"]


def test_listing_marks_entry_names():
    listing = str(psf_parser.Database(RUNS_DIR / "device_match@25.1" / "ascii"))
    assert "mytemp-000_myswept-dcmatch   (entry name, no netlist path)" in listing


def test_shared_path_falls_back_to_entry_names(tmp_path):
    folder = _copy(tmp_path, "default_precision@25.1")
    _edit_logfile(folder, '"myac-ac"', '"myop-ac"')
    db = psf_parser.Database(folder)
    assert list(db.analyses) == ["myop-dc", "mydc", "myop-ac", "mytran"]
    assert not db.entry("myop-dc").has_path


def test_entry_with_missing_parent_is_its_own_analysis(tmp_path):
    folder = _copy(tmp_path, "sweeps@25.1")
    _edit_logfile(folder, '"PSF"\n"mypairs_ac1-sweep"', '"PSF"\n"gone-sweep"', count=1)
    db = psf_parser.Database(folder)
    assert db["mypairs/ac1"]._levels[0].counts == (2,)
    assert not db.entry("mypairs-000_ac1-ac").has_path


def test_missing_lists_deleted_leaf_files(tmp_path):
    folder = _copy(tmp_path, "rc_lowpass@25.1", "binary")
    gone = folder / "mysweep-001_mynestedsweep-002_ac2.ac"
    gone.unlink()
    db = psf_parser.Database(folder)
    assert db["mysweep/mynestedsweep/ac2"].missing == (gone,)
    assert db["mysweep/ac1"].missing == ()


def test_folder_without_logfile_points_to_load(tmp_path):
    with pytest.raises(FileNotFoundError, match=r"psf_parser\.load"):
        psf_parser.Database(tmp_path)


def test_logfile_entries_need_analysis_fields(tmp_path):
    # An operating point is a PSF file of named entries, but not a logFile.
    shutil.copy(RUNS_DIR / "default_precision@25.1" / "ascii" / "myop.dc", tmp_path / "logFile")
    with pytest.raises(psf_parser.PsfParseError, match="lacks the fields"):
        psf_parser.Database(tmp_path)


def test_entry_inside_a_tree_names_its_analysis():
    db = psf_parser.Database(RUNS_DIR / "rc_lowpass@25.1" / "ascii")
    with pytest.raises(KeyError, match=r"inside the analysis 'mysweep/mynestedsweep/ac2'"):
        db.entry("mysweep-001_mynestedsweep-002_ac2-ac")
    with pytest.raises(KeyError, match="no logFile entry"):
        db.entry("nothing")


def test_entry_name_given_as_path_suggests_entry():
    db = psf_parser.Database(RUNS_DIR / "rc_lowpass@25.1" / "ascii")
    with pytest.raises(KeyError, match=r"use db\.entry\(\)"):
        _ = db["mysweep_ac2-sweep"]
