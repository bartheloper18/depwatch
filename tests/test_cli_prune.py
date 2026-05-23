"""Tests for depwatch.cli_prune."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from depwatch.cli_prune import _cmd_prune


class _FakeArgs:
    def __init__(self, config: str, max_entries: int = 100, max_age_days: int = 30):
        self.config = config
        self.max_entries = max_entries
        self.max_age_days = max_age_days


def _entry(days_ago: float = 0) -> dict:
    ts = (datetime.now(tz=timezone.utc) - timedelta(days=days_ago)).isoformat()
    return {"timestamp": ts, "project": "p", "outdated": []}


@pytest.fixture()
def project_dir(tmp_path: Path):
    history = tmp_path / "history.json"
    config = {
        "projects": [],
        "history_path": str(history),
        "check_interval_seconds": 3600,
        "alert_cooldown_seconds": 86400,
        "alert_state_path": str(tmp_path / "alert.json"),
    }
    cfg_path = tmp_path / "depwatch.json"
    cfg_path.write_text(json.dumps(config))
    return tmp_path, cfg_path, history


def test_cmd_prune_no_history_file(project_dir, capsys):
    _, cfg_path, _ = project_dir
    args = _FakeArgs(config=str(cfg_path))
    rc = _cmd_prune(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "Nothing to prune" in captured.out


def test_cmd_prune_removes_old_entries(project_dir, capsys):
    _, cfg_path, history = project_dir
    entries = [_entry(days_ago=40), _entry(days_ago=1)]
    history.write_text(json.dumps(entries))

    args = _FakeArgs(config=str(cfg_path), max_age_days=30)
    rc = _cmd_prune(args)
    assert rc == 0

    saved = json.loads(history.read_text())
    assert len(saved) == 1
    captured = capsys.readouterr()
    assert "Pruned 1" in captured.out


def test_cmd_prune_nothing_to_remove(project_dir, capsys):
    _, cfg_path, history = project_dir
    entries = [_entry(days_ago=1)]
    history.write_text(json.dumps(entries))

    args = _FakeArgs(config=str(cfg_path), max_age_days=30, max_entries=100)
    rc = _cmd_prune(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "Nothing to prune" in captured.out


def test_cmd_prune_respects_max_entries(project_dir, capsys):
    _, cfg_path, history = project_dir
    entries = [_entry(days_ago=i) for i in range(10)]
    history.write_text(json.dumps(entries))

    args = _FakeArgs(config=str(cfg_path), max_entries=3, max_age_days=365)
    rc = _cmd_prune(args)
    assert rc == 0

    saved = json.loads(history.read_text())
    assert len(saved) == 3
