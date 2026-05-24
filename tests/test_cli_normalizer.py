"""Tests for depwatch.cli_normalizer."""
import json
import pytest
from unittest.mock import patch, MagicMock

from depwatch.cli_normalizer import _result_from_entry, _cmd_normalizer, add_normalizer_subcommand


class _FakeArgs:
    def __init__(self, history="depwatch_history.json", as_json=False):
        self.history = history
        self.as_json = as_json


def _entry(project="proj", pkgs=None):
    pkgs = pkgs or []
    return {"project": project, "packages": pkgs}


def _pkg(name, current, latest, outdated):
    return {
        "name": name,
        "current_version": current,
        "latest_version": latest,
        "is_outdated": outdated,
    }


def test_result_from_entry_empty_packages():
    result = _result_from_entry(_entry())
    assert result.project == "proj"
    assert result.packages == []


def test_result_from_entry_with_packages():
    e = _entry(pkgs=[_pkg("requests", "2.0", "2.1", True)])
    result = _result_from_entry(e)
    assert len(result.packages) == 1
    assert result.packages[0].name == "requests"


def test_cmd_normalizer_no_history(capsys):
    with patch("depwatch.cli_normalizer.load_history", return_value=[]):
        rc = _cmd_normalizer(_FakeArgs())
    assert rc == 1
    captured = capsys.readouterr()
    assert "No history" in captured.err


def test_cmd_normalizer_text_output(capsys):
    entries = [_entry("myproj", [_pkg("flask", "2.0.0", "2.3.0", True)])]
    with patch("depwatch.cli_normalizer.load_history", return_value=entries):
        rc = _cmd_normalizer(_FakeArgs(as_json=False))
    assert rc == 0
    out = capsys.readouterr().out
    assert "myproj" in out


def test_cmd_normalizer_json_output(capsys):
    entries = [_entry("proj2", [_pkg("numpy", "1.0.0", "2.0.0", True)])]
    with patch("depwatch.cli_normalizer.load_history", return_value=entries):
        rc = _cmd_normalizer(_FakeArgs(as_json=True))
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["project"] == "proj2"
    assert data[0]["packages"][0]["name"] == "numpy"
    assert "current_parts" in data[0]["packages"][0]


def test_add_normalizer_subcommand_registers():
    import argparse
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_normalizer_subcommand(subs)
    args = parser.parse_args(["normalize", "--history", "foo.json"])
    assert args.history == "foo.json"
    assert args.func is not None
