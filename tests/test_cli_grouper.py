"""Tests for depwatch.cli_grouper."""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

from depwatch.cli_grouper import _cmd_grouper, _result_from_entry


class _FakeArgs:
    def __init__(self, history: str, project=None):
        self.history = history
        self.project = project


def _entry(project_name: str, packages: list) -> dict:
    return {"project_name": project_name, "packages": packages, "timestamp": "2024-01-01T00:00:00"}


def _pkg(name: str, current: str, latest: str, outdated: bool = True) -> dict:
    return {"name": name, "current_version": current, "latest_version": latest, "outdated": outdated}


@pytest.fixture()
def hist_path(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path / "history.json"


def test_cmd_grouper_no_history(hist_path, capsys):
    args = _FakeArgs(history=str(hist_path))
    with pytest.raises(SystemExit) as exc:
        _cmd_grouper(args)
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "No history" in captured.err


def test_cmd_grouper_prints_sections(hist_path, capsys):
    data = [
        _entry("myproj", [
            _pkg("requests", "2.0.0", "3.0.0", outdated=True),
            _pkg("flask", "1.0.0", "1.0.0", outdated=False),
        ])
    ]
    hist_path.write_text(json.dumps(data))
    args = _FakeArgs(history=str(hist_path))
    _cmd_grouper(args)
    out = capsys.readouterr().out
    assert "myproj" in out
    assert "Critical" in out
    assert "Up-to-date" in out


def test_result_from_entry_builds_check_result():
    entry = _entry("proj", [_pkg("django", "3.0", "4.0")])
    result = _result_from_entry(entry)
    assert result.project_name == "proj"
    assert len(result.packages) == 1
    assert result.packages[0].name == "django"


def test_result_from_entry_empty_packages():
    entry = _entry("empty", [])
    result = _result_from_entry(entry)
    assert result.packages == []
