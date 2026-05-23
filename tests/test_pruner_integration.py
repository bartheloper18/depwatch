"""Integration tests for pruner interacting with history module."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from depwatch.history import load_history, save_history
from depwatch.pruner import prune_history


def _ts(days_ago: float) -> str:
    return (datetime.now(tz=timezone.utc) - timedelta(days=days_ago)).isoformat()


def _make_entry(days_ago: float, project: str = "myproject") -> dict:
    return {
        "timestamp": _ts(days_ago),
        "project": project,
        "outdated": [{"name": "requests", "current": "2.28.0", "latest": "2.31.0"}],
    }


@pytest.fixture()
def hist_file(tmp_path: Path) -> Path:
    return tmp_path / "history.json"


def test_roundtrip_prune_preserves_recent(hist_file):
    entries = [_make_entry(i) for i in range(5)]
    save_history(str(hist_file), entries)

    removed = prune_history(str(hist_file), max_entries=10, max_age_days=30)
    assert removed == 0

    loaded = load_history(str(hist_file))
    assert len(loaded) == 5


def test_roundtrip_prune_removes_stale(hist_file):
    recent = [_make_entry(i) for i in range(3)]
    old = [_make_entry(60), _make_entry(90)]
    save_history(str(hist_file), recent + old)

    removed = prune_history(str(hist_file), max_entries=100, max_age_days=30)
    assert removed == 2

    loaded = load_history(str(hist_file))
    assert len(loaded) == 3


def test_roundtrip_prune_max_entries_respected(hist_file):
    entries = [_make_entry(i) for i in range(20)]
    save_history(str(hist_file), entries)

    removed = prune_history(str(hist_file), max_entries=5, max_age_days=365)
    assert removed == 15

    loaded = load_history(str(hist_file))
    assert len(loaded) == 5


def test_prune_empty_history_is_noop(hist_file):
    save_history(str(hist_file), [])
    removed = prune_history(str(hist_file))
    assert removed == 0
    assert load_history(str(hist_file)) == []
