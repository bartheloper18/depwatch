"""Tests for depwatch.pruner."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from depwatch.pruner import (
    DEFAULT_MAX_AGE_DAYS,
    DEFAULT_MAX_ENTRIES,
    prune_by_age,
    prune_by_count,
    prune_history,
)


def _entry(days_ago: float = 0, project: str = "proj") -> dict:
    ts = (datetime.now(tz=timezone.utc) - timedelta(days=days_ago)).isoformat()
    return {"timestamp": ts, "project": project, "outdated": []}


@pytest.fixture()
def hist_path(tmp_path: Path) -> str:
    return str(tmp_path / "history.json")


# --- prune_by_count ---

def test_prune_by_count_keeps_all_when_under_limit():
    entries = [_entry() for _ in range(5)]
    result = prune_by_count(entries, max_entries=10)
    assert len(result) == 5


def test_prune_by_count_trims_oldest():
    entries = [_entry(days_ago=i) for i in range(10)]
    result = prune_by_count(entries, max_entries=3)
    assert len(result) == 3
    # Should keep the last 3 (most recent = smallest days_ago)
    assert result == entries[-3:]


def test_prune_by_count_exact_limit():
    entries = [_entry() for _ in range(DEFAULT_MAX_ENTRIES)]
    result = prune_by_count(entries)
    assert len(result) == DEFAULT_MAX_ENTRIES


# --- prune_by_age ---

def test_prune_by_age_keeps_recent():
    entries = [_entry(days_ago=1), _entry(days_ago=2)]
    result = prune_by_age(entries, max_age_days=7)
    assert len(result) == 2


def test_prune_by_age_removes_old():
    entries = [_entry(days_ago=40), _entry(days_ago=1)]
    result = prune_by_age(entries, max_age_days=30)
    assert len(result) == 1
    assert result[0]["timestamp"] == entries[1]["timestamp"]


def test_prune_by_age_keeps_entry_without_timestamp():
    entries = [{"project": "x", "outdated": []}]
    result = prune_by_age(entries, max_age_days=1)
    assert len(result) == 1


def test_prune_by_age_keeps_entry_with_bad_timestamp():
    entries = [{"timestamp": "not-a-date", "project": "x"}]
    result = prune_by_age(entries, max_age_days=1)
    assert len(result) == 1


# --- prune_history (integration) ---

def test_prune_history_missing_file_returns_zero(hist_path):
    removed = prune_history(hist_path)
    assert removed == 0


def test_prune_history_removes_old_entries(hist_path):
    entries = [_entry(days_ago=40), _entry(days_ago=1)]
    with open(hist_path, "w") as f:
        json.dump(entries, f)

    removed = prune_history(hist_path, max_age_days=30)
    assert removed == 1

    with open(hist_path) as f:
        saved = json.load(f)
    assert len(saved) == 1


def test_prune_history_no_change_does_not_rewrite(hist_path):
    entries = [_entry(days_ago=1)]
    with open(hist_path, "w") as f:
        json.dump(entries, f)

    mtime_before = os.path.getmtime(hist_path)
    removed = prune_history(hist_path, max_age_days=30, max_entries=100)
    assert removed == 0
    assert os.path.getmtime(hist_path) == mtime_before
