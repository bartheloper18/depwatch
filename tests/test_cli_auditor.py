"""Tests for depwatch.cli_auditor"""
from __future__ import annotations

import json
import pathlib

import pytest

from depwatch.cli_auditor import _cmd_auditor, _result_from_entry


class _FakeArgs:
    def __init__(self, history, project=None, min_severity="low"):
        self.history = history
        self.project = project
        self.min_severity = min_severity


def _entry(project="myapp", packages=None):
    return {
        "project": project,
        "timestamp": "2024-01-01T00:00:00",
        "packages": packages or [],
    }


def _pkg(name, current, latest, outdated):
    return {
        "name": name,
        "current_version": current,
        "latest_version": latest,
        "is_outdated": outdated,
    }


def test_cmd_auditor_no_history(tmp_path):
    args = _FakeArgs(history=str(tmp_path / "missing.json"))
    rc = _cmd_auditor(args)
    assert rc == 1


def test_cmd_auditor_all_up_to_date(tmp_path, capsys):
    hist = tmp_path / "h.json"
    hist.write_text(json.dumps([_entry(packages=[_pkg("lib", "1.0", "1.0", False)])]))
    args = _FakeArgs(history=str(hist))
    rc = _cmd_auditor(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No findings" in out


def test_cmd_auditor_critical_finding(tmp_path, capsys):
    hist = tmp_path / "h.json"
    hist.write_text(
        json.dumps([_entry(packages=[_pkg("requests", "1.0.0", "3.0.0", True)])])
    )
    args = _FakeArgs(history=str(hist))
    rc = _cmd_auditor(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "CRITICAL" in out
    assert "requests" in out


def test_cmd_auditor_min_severity_filters_low(tmp_path, capsys):
    hist = tmp_path / "h.json"
    hist.write_text(
        json.dumps(
            [
                _entry(
                    packages=[
                        _pkg("lib_low", "1.0.0", "1.0.1", True),
                        _pkg("lib_crit", "1.0.0", "3.0.0", True),
                    ]
                )
            ]
        )
    )
    args = _FakeArgs(history=str(hist), min_severity="high")
    rc = _cmd_auditor(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "lib_crit" in out
    assert "lib_low" not in out


def test_result_from_entry_builds_check_result():
    entry = _entry(packages=[_pkg("flask", "2.0", "3.0", True)])
    result = _result_from_entry(entry)
    assert result.project == "myapp"
    assert len(result.packages) == 1
    assert result.packages[0].name == "flask"
