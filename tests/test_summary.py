"""Tests for depwatch.summary."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import pytest

from depwatch.summary import summarise, format_summary, ProjectSummary


@pytest.fixture()
def hist_path(tmp_path):
    return str(tmp_path / "history.json")


def _write_history(path: str, entries: list) -> None:
    with open(path, "w") as fh:
        json.dump(entries, fh)


def test_summarise_empty_file(hist_path):
    _write_history(hist_path, [])
    result = summarise(hist_path)
    assert result == []


def test_summarise_missing_file(hist_path):
    # load_history returns [] for missing file
    result = summarise(hist_path)
    assert result == []


def test_summarise_single_project_up_to_date(hist_path):
    _write_history(hist_path, [
        {
            "project_path": "/proj/a",
            "checked_at": "2024-01-15T10:00:00",
            "outdated_packages": [],
        }
    ])
    summaries = summarise(hist_path)
    assert len(summaries) == 1
    s = summaries[0]
    assert s.project_path == "/proj/a"
    assert s.total_checks == 1
    assert s.last_outdated_count == 0
    assert s.ever_had_outdated is False


def test_summarise_single_project_outdated(hist_path):
    _write_history(hist_path, [
        {
            "project_path": "/proj/b",
            "checked_at": "2024-03-01T08:30:00",
            "outdated_packages": [{"name": "requests", "current": "2.28.0", "latest": "2.31.0"}],
        }
    ])
    summaries = summarise(hist_path)
    assert summaries[0].last_outdated_count == 1
    assert summaries[0].ever_had_outdated is True


def test_summarise_multiple_checks_picks_latest(hist_path):
    _write_history(hist_path, [
        {"project_path": "/proj/c", "checked_at": "2024-01-01T00:00:00", "outdated_packages": [{"name": "x"}]},
        {"project_path": "/proj/c", "checked_at": "2024-06-01T12:00:00", "outdated_packages": []},
    ])
    summaries = summarise(hist_path)
    assert len(summaries) == 1
    s = summaries[0]
    assert s.total_checks == 2
    assert s.last_outdated_count == 0   # latest check is clean
    assert s.ever_had_outdated is True  # but history shows it was outdated


def test_summarise_multiple_projects(hist_path):
    _write_history(hist_path, [
        {"project_path": "/proj/a", "checked_at": "2024-01-01T00:00:00", "outdated_packages": []},
        {"project_path": "/proj/b", "checked_at": "2024-01-02T00:00:00", "outdated_packages": []},
    ])
    summaries = summarise(hist_path)
    assert len(summaries) == 2


def test_format_summary_no_history(hist_path):
    text = format_summary(hist_path)
    assert text == "No history recorded yet."


def test_format_summary_contains_project_path(hist_path):
    _write_history(hist_path, [
        {"project_path": "/my/project", "checked_at": "2024-05-10T09:00:00", "outdated_packages": []},
    ])
    text = format_summary(hist_path)
    assert "/my/project" in text
    assert "depwatch summary" in text


def test_project_summary_str_outdated():
    s = ProjectSummary(
        project_path="/p",
        total_checks=3,
        last_checked=datetime(2024, 6, 1, 12, 0, tzinfo=timezone.utc),
        last_outdated_count=2,
        ever_had_outdated=True,
    )
    assert "2 outdated" in str(s)
    assert "/p" in str(s)
