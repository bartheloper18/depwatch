"""Tests for depwatch.cli_filterer."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from depwatch.cli_filterer import _cmd_filterer, _result_from_entry


class _FakeArgs:
    def __init__(self, history, only_outdated=False, name_contains=None,
                 min_bump=None, project_types=None):
        self.history = history
        self.only_outdated = only_outdated
        self.name_contains = name_contains
        self.min_bump = min_bump
        self.project_types = project_types or []


def _entry(project_name="myapp", project_type="python", packages=None):
    return {
        "project_name": project_name,
        "project_type": project_type,
        "checked_at": "2024-01-01T00:00:00",
        "packages": packages or [],
    }


def _pkg(name, cur, lat, outdated):
    return {"name": name, "current_version": cur,
            "latest_version": lat, "is_outdated": outdated}


def test_cmd_filterer_no_history(tmp_path, capsys):
    args = _FakeArgs(history=str(tmp_path / "missing.json"))
    _cmd_filterer(args)
    captured = capsys.readouterr()
    assert "No history" in captured.err


def test_cmd_filterer_no_filter_prints_all(tmp_path, capsys):
    hist = tmp_path / "hist.json"
    pkgs = [_pkg("requests", "2.0", "3.0", True)]
    hist.write_text(json.dumps([_entry(packages=pkgs)]))
    args = _FakeArgs(history=str(hist))
    _cmd_filterer(args)
    captured = capsys.readouterr()
    assert "requests" in captured.out


def test_cmd_filterer_only_outdated(tmp_path, capsys):
    hist = tmp_path / "hist.json"
    pkgs = [
        _pkg("requests", "2.0", "3.0", True),
        _pkg("flask", "1.0", "1.0", False),
    ]
    hist.write_text(json.dumps([_entry(packages=pkgs)]))
    args = _FakeArgs(history=str(hist), only_outdated=True)
    _cmd_filterer(args)
    captured = capsys.readouterr()
    assert "requests" in captured.out
    assert "flask" not in captured.out


def test_cmd_filterer_name_contains(tmp_path, capsys):
    hist = tmp_path / "hist.json"
    pkgs = [
        _pkg("requests", "2.0", "3.0", True),
        _pkg("flask", "1.0", "2.0", True),
    ]
    hist.write_text(json.dumps([_entry(packages=pkgs)]))
    args = _FakeArgs(history=str(hist), name_contains="flask")
    _cmd_filterer(args)
    captured = capsys.readouterr()
    assert "flask" in captured.out
    assert "requests" not in captured.out


def test_result_from_entry_builds_correctly():
    entry = _entry(packages=[_pkg("a", "1.0", "2.0", True)])
    result = _result_from_entry(entry)
    assert result.project_name == "myapp"
    assert len(result.packages) == 1
    assert result.packages[0].name == "a"
    assert result.packages[0].is_outdated is True
