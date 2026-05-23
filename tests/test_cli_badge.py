"""Tests for depwatch.cli_badge."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from depwatch.cli_badge import _cmd_badge, _result_from_entry
from depwatch.history import save_history


class _FakeArgs:
    def __init__(
        self,
        history_file: Path,
        out: Path | None = None,
        project: str | None = None,
    ):
        self.history_file = history_file
        self.out = out
        self.project = project


def _entry(project: str, outdated: int, up_to_date: int) -> dict:
    packages = [
        {"name": f"pkg-out-{i}", "current": "1.0", "latest": "2.0", "outdated": True}
        for i in range(outdated)
    ]
    packages += [
        {"name": f"pkg-ok-{i}", "current": "1.0", "latest": "1.0", "outdated": False}
        for i in range(up_to_date)
    ]
    return {"project": project, "timestamp": "2024-01-01T00:00:00", "packages": packages}


def test_cmd_badge_no_history(tmp_path: Path):
    args = _FakeArgs(history_file=tmp_path / "missing.json")
    assert _cmd_badge(args) == 1


def test_cmd_badge_prints_json(tmp_path: Path, capsys):
    hist = tmp_path / "history.json"
    save_history(hist, [_entry("myapp", outdated=0, up_to_date=4)])
    args = _FakeArgs(history_file=hist)
    rc = _cmd_badge(args)
    assert rc == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["label"] == "myapp"
    assert data["message"] == "up to date"
    assert data["color"] == "brightgreen"


def test_cmd_badge_writes_file(tmp_path: Path):
    hist = tmp_path / "history.json"
    save_history(hist, [_entry("proj", outdated=2, up_to_date=6)])
    out = tmp_path / "badge.json"
    args = _FakeArgs(history_file=hist, out=out)
    rc = _cmd_badge(args)
    assert rc == 0
    assert out.exists()
    data = json.loads(out.read_text())
    assert "2/8" in data["message"]


def test_result_from_entry_maps_packages():
    entry = _entry("x", outdated=1, up_to_date=2)
    result = _result_from_entry(entry)
    assert result.project_name == "x"
    assert len(result.packages) == 3
    assert sum(1 for p in result.packages if p.outdated) == 1
