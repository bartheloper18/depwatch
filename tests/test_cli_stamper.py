"""Tests for depwatch.cli_stamper."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from depwatch.cli_stamper import _cmd_stamper, _result_from_entry


class _FakeArgs:
    def __init__(self, history: str, as_json: bool = False):
        self.history = history
        self.as_json = as_json


def _entry(project: str = "proj", outdated: bool = False) -> dict:
    return {
        "project": project,
        "project_type": "python",
        "packages": [
            {
                "name": "requests",
                "current_version": "2.28.0",
                "latest_version": "2.31.0",
                "is_outdated": outdated,
            }
        ],
    }


def test_cmd_stamper_no_history(tmp_path):
    args = _FakeArgs(history=str(tmp_path / "missing.json"))
    assert _cmd_stamper(args) == 1


def test_cmd_stamper_empty_history(tmp_path):
    hist = tmp_path / "hist.json"
    hist.write_text(json.dumps([]))
    args = _FakeArgs(history=str(hist))
    assert _cmd_stamper(args) == 1


def test_cmd_stamper_text_output(tmp_path, capsys):
    hist = tmp_path / "hist.json"
    hist.write_text(json.dumps([_entry(outdated=True)]))
    args = _FakeArgs(history=str(hist))
    rc = _cmd_stamper(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "proj" in out
    assert "requests" in out


def test_cmd_stamper_json_output(tmp_path, capsys):
    hist = tmp_path / "hist.json"
    hist.write_text(json.dumps([_entry(outdated=False)]))
    args = _FakeArgs(history=str(hist), as_json=True)
    rc = _cmd_stamper(args)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["project"] == "proj"
    assert "stamped_at" in data
    assert "packages" in data
    assert data["packages"][0]["age_seconds"] >= 0


def test_result_from_entry_maps_fields():
    entry = _entry(outdated=True)
    result = _result_from_entry(entry)
    assert result.project == "proj"
    assert len(result.packages) == 1
    assert result.packages[0].is_outdated is True


def test_result_from_entry_empty_packages():
    entry = {"project": "x", "project_type": "node", "packages": []}
    result = _result_from_entry(entry)
    assert result.packages == []
