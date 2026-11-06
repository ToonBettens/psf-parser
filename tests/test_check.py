"""The rules in `psf_parser._check`, directly and through a parser."""

from __future__ import annotations

import re

import pytest

import psf_parser
from psf_parser._check import add_type, add_variable, check
from psf_parser.errors import PsfStructureError
from psf_parser.model import Kind, PsfFile, PsfType, Role, Variable

FLOAT = PsfType("V", Kind.FLOAT64)


def _myac_text(run) -> str:
    return next(s for s in run.samples("ascii") if s.path.name == "myac.ac").path.read_text()


def test_equal_columns_pass():
    file = PsfFile()
    add_variable(file, Variable("freq", FLOAT, Role.SWEEP, values=[1.0, 2.0]))
    add_variable(file, Variable("out", FLOAT, Role.TRACE, values=[3.0, 4.0]))
    check(file)


def test_unequal_columns_raise():
    file = PsfFile()
    add_variable(file, Variable("freq", FLOAT, Role.SWEEP, values=[1.0, 2.0]))
    add_variable(file, Variable("out", FLOAT, Role.TRACE, values=[3.0]))
    with pytest.raises(PsfStructureError):
        check(file)


def test_entries_of_any_length_pass():
    file = PsfFile()
    add_variable(file, Variable("a", FLOAT, Role.ENTRY, values=[1.0]))
    add_variable(file, Variable("b", FLOAT, Role.ENTRY, values=[]))
    check(file)


def test_duplicate_variable_raises():
    file = PsfFile()
    add_variable(file, Variable("out", FLOAT, Role.SWEEP))
    with pytest.raises(PsfStructureError):
        add_variable(file, Variable("out", FLOAT, Role.TRACE))


def test_duplicate_type_raises():
    file = PsfFile()
    add_type(file, FLOAT)
    with pytest.raises(PsfStructureError):
        add_type(file, FLOAT)


def test_load_raises_on_a_missing_value(run, tmp_path):
    text = _myac_text(run)
    value = text.index("\nVALUE\n")
    damaged = text[:value] + re.sub(r'"out" \(.*\)\n', "", text[value:], count=1)
    path = tmp_path / "myac.ac"
    path.write_text(damaged)
    file = psf_parser.load(path)
    with pytest.raises(PsfStructureError):
        _ = file["out"].values


def test_load_raises_on_a_value_for_an_undeclared_variable(run, tmp_path):
    text = _myac_text(run)
    value = text.index("\nVALUE\n")
    path = tmp_path / "myac.ac"
    path.write_text(text[:value] + text[value:].replace('"out" (', '"nope" (', 1))
    file = psf_parser.load(path)
    with pytest.raises(PsfStructureError):
        _ = file["out"].values
