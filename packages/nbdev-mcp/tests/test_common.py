"""Tests for nbdev_mcp.tools._common."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from nbdev_mcp.tools._common import (
    classify_cell,
    find_notebooks,
    generate_cell_id,
    get_directives,
    get_source,
    load_notebook,
    parse_spec,
    save_notebook,
    source_to_array,
    validate_notebook_path,
    validate_path,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cell(cell_type="code", source=""):
    return {"cell_type": cell_type, "source": source, "outputs": [], "id": "aabbccdd"}


def _make_notebook(cells=None):
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {},
        "cells": cells or [],
    }


# ---------------------------------------------------------------------------
# get_source
# ---------------------------------------------------------------------------

class TestGetSource:
    def test_string_source(self):
        cell = _make_cell(source="hello world")
        assert get_source(cell) == "hello world"

    def test_list_source(self):
        cell = _make_cell(source=["line1\n", "line2"])
        assert get_source(cell) == "line1\nline2"

    def test_empty_string(self):
        cell = _make_cell(source="")
        assert get_source(cell) == ""

    def test_empty_list(self):
        cell = _make_cell(source=[])
        assert get_source(cell) == ""

    def test_missing_source_key(self):
        assert get_source({}) == ""


# ---------------------------------------------------------------------------
# source_to_array
# ---------------------------------------------------------------------------

class TestSourceToArray:
    def test_single_line(self):
        assert source_to_array("hello") == ["hello"]

    def test_multiline(self):
        result = source_to_array("a\nb\nc")
        assert result == ["a\n", "b\n", "c"]

    def test_empty(self):
        assert source_to_array("") == []

    def test_trailing_newline_not_duplicated(self):
        # "a\n" splits into ["a", ""] — the empty trailing part is dropped
        result = source_to_array("a\n")
        assert result == ["a\n"]

    def test_roundtrip(self):
        original = "x = 1\ny = 2\nz = x + y"
        assert "".join(source_to_array(original)) == original


# ---------------------------------------------------------------------------
# get_directives
# ---------------------------------------------------------------------------

class TestGetDirectives:
    def test_no_directives(self):
        assert get_directives("x = 1") == []

    def test_single_directive(self):
        assert get_directives("#| export\nx = 1") == ["#| export"]

    def test_multiple_directives(self):
        src = "#| export\n#| hide\nx = 1"
        assert get_directives(src) == ["#| export", "#| hide"]

    def test_stops_at_non_comment(self):
        src = "#| export\nx = 1\n#| this is ignored"
        assert get_directives(src) == ["#| export"]

    def test_ignores_regular_comments(self):
        # A regular `#` comment (not `#|`) ends the directive block
        src = "#| export\n# note\nx = 1"
        assert get_directives(src) == ["#| export"]

    def test_empty_source(self):
        assert get_directives("") == []


# ---------------------------------------------------------------------------
# classify_cell
# ---------------------------------------------------------------------------

class TestClassifyCell:
    def test_markdown_cell(self):
        cell = _make_cell(cell_type="markdown", source="# Hello")
        assert classify_cell(cell) == "markdown"

    def test_export(self):
        cell = _make_cell(source="#| export\ndef foo(): pass")
        assert classify_cell(cell) == "export"

    def test_exporti(self):
        cell = _make_cell(source="#| exporti\ndef foo(): pass")
        assert classify_cell(cell) == "exporti"

    def test_exports(self):
        cell = _make_cell(source="#| exports\ndef foo(): pass")
        assert classify_cell(cell) == "exports"

    def test_default_exp(self):
        cell = _make_cell(source="#| default_exp core")
        assert classify_cell(cell) == "default_exp"

    def test_hidden(self):
        cell = _make_cell(source="#| hide\nx = 1")
        assert classify_cell(cell) == "hidden"

    def test_test_cell(self):
        cell = _make_cell(source="assert 1 + 1 == 2")
        assert classify_cell(cell) == "test"

    def test_empty_code_cell(self):
        cell = _make_cell(source="")
        assert classify_cell(cell) == "test"


# ---------------------------------------------------------------------------
# generate_cell_id
# ---------------------------------------------------------------------------

class TestGenerateCellId:
    def test_deterministic(self):
        a = generate_cell_id(0, "content")
        b = generate_cell_id(0, "content")
        assert a == b

    def test_different_index(self):
        assert generate_cell_id(0, "x") != generate_cell_id(1, "x")

    def test_different_content(self):
        assert generate_cell_id(0, "a") != generate_cell_id(0, "b")

    def test_length(self):
        assert len(generate_cell_id(0, "")) == 8

    def test_hex_chars(self):
        cid = generate_cell_id(3, "hello")
        assert all(c in "0123456789abcdef" for c in cid)


# ---------------------------------------------------------------------------
# parse_spec
# ---------------------------------------------------------------------------

class TestParseSpec:
    def test_single_code_cell(self):
        spec = "code\nx = 1"
        result = parse_spec(spec)
        assert result == [("code", "x = 1")]

    def test_multiple_cells(self):
        spec = "code\nx = 1\n---\nmarkdown\n# Hello"
        result = parse_spec(spec)
        assert len(result) == 2
        assert result[0] == ("code", "x = 1")
        assert result[1] == ("markdown", "# Hello")

    def test_skips_unknown_type(self):
        spec = "unknown\nstuff\n---\ncode\nx = 1"
        result = parse_spec(spec)
        assert result == [("code", "x = 1")]

    def test_empty_spec(self):
        assert parse_spec("") == []

    def test_raw_cell(self):
        result = parse_spec("raw\nsome raw content")
        assert result == [("raw", "some raw content")]


# ---------------------------------------------------------------------------
# find_notebooks
# ---------------------------------------------------------------------------

class TestFindNotebooks:
    def test_single_file(self, tmp_path):
        nb = tmp_path / "test.ipynb"
        nb.touch()
        assert find_notebooks(str(nb)) == [nb]

    def test_non_notebook_file(self, tmp_path):
        f = tmp_path / "script.py"
        f.touch()
        assert find_notebooks(str(f)) == []

    def test_directory(self, tmp_path):
        (tmp_path / "a.ipynb").touch()
        (tmp_path / "b.ipynb").touch()
        (tmp_path / "c.py").touch()
        result = find_notebooks(str(tmp_path))
        names = {p.name for p in result}
        assert names == {"a.ipynb", "b.ipynb"}

    def test_skips_checkpoints(self, tmp_path):
        checkpoints = tmp_path / ".ipynb_checkpoints"
        checkpoints.mkdir()
        (checkpoints / "x.ipynb").touch()
        (tmp_path / "real.ipynb").touch()
        result = find_notebooks(str(tmp_path))
        assert len(result) == 1
        assert result[0].name == "real.ipynb"

    def test_nonexistent(self, tmp_path):
        assert find_notebooks(str(tmp_path / "nope")) == []


# ---------------------------------------------------------------------------
# load_notebook / save_notebook
# ---------------------------------------------------------------------------

class TestLoadSaveNotebook:
    def test_roundtrip(self, tmp_path):
        nb = _make_notebook([_make_cell(source="x = 1")])
        path = tmp_path / "test.ipynb"
        save_notebook(nb, path)
        loaded = load_notebook(path)
        assert loaded["cells"][0]["source"] == "x = 1"

    def test_save_adds_trailing_newline(self, tmp_path):
        nb = _make_notebook()
        path = tmp_path / "test.ipynb"
        save_notebook(nb, path)
        assert path.read_text().endswith("\n")

    def test_save_uses_sort_keys(self, tmp_path):
        nb = {"z": 1, "a": 2, "m": 3}
        path = tmp_path / "test.ipynb"
        save_notebook(nb, path)
        text = path.read_text()
        pos_a = text.index('"a"')
        pos_m = text.index('"m"')
        pos_z = text.index('"z"')
        assert pos_a < pos_m < pos_z


# ---------------------------------------------------------------------------
# validate_notebook_path
# ---------------------------------------------------------------------------

class TestValidateNotebookPath:
    def test_valid_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        nb = tmp_path / "test.ipynb"
        nb.touch()
        p, err = validate_notebook_path(str(nb))
        assert err is None
        assert p == nb.resolve()

    def test_not_ipynb(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        f = tmp_path / "test.py"
        f.touch()
        p, err = validate_notebook_path(str(f))
        assert err is not None
        assert "not a .ipynb" in err

    def test_outside_project(self, tmp_path, monkeypatch):
        project = tmp_path / "project"
        project.mkdir()
        monkeypatch.chdir(project)
        nb = tmp_path / "outside.ipynb"
        nb.touch()
        p, err = validate_notebook_path(str(nb))
        assert err is not None
        assert "outside" in err

    def test_not_found(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        p, err = validate_notebook_path(str(tmp_path / "missing.ipynb"))
        assert err is not None
        assert "not found" in err

    def test_must_exist_false(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        p, err = validate_notebook_path(str(tmp_path / "new.ipynb"), must_exist=False)
        assert err is None


# ---------------------------------------------------------------------------
# validate_path
# ---------------------------------------------------------------------------

class TestValidatePath:
    def test_valid_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        f = tmp_path / "spec.txt"
        f.touch()
        p, err = validate_path(str(f))
        assert err is None

    def test_outside_project(self, tmp_path, monkeypatch):
        project = tmp_path / "project"
        project.mkdir()
        monkeypatch.chdir(project)
        f = tmp_path / "outside.txt"
        f.touch()
        p, err = validate_path(str(f))
        assert err is not None
