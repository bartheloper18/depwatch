"""Tests for depwatch.history."""

import json
import os

import pytest

from depwatch.checker import CheckResult, PackageStatus
from depwatch.history import (
    DEFAULT_HISTORY_PATH,
    MAX_HISTORY_ENTRIES,
    _entry_from_result,
    latest_entry,
    load_history,
    record_result,
    save_history,
)


def _make_result(project="myapp", ptype="python"):
    packages = [
        PackageStatus("requests", "2.28.0", "2.31.0"),
        PackageStatus("flask", "3.0.0", "3.0.0"),
    ]
    return CheckResult(project_name=project, project_type=ptype, packages=packages)


@pytest.fixture()
def hist_path(tmp_path):
    return str(tmp_path / "history.json")


def test_load_history_missing_file(hist_path):
    assert load_history(hist_path) == []


def test_load_history_malformed_file(hist_path):
    os.makedirs(os.path.dirname(hist_path), exist_ok=True)
    with open(hist_path, "w") as fh:
        fh.write("not json{{{")
    assert load_history(hist_path) == []


def test_save_and_load_roundtrip(hist_path):
    entries = [{"project": "demo", "outdated": 1}]
    save_history(entries, hist_path)
    loaded = load_history(hist_path)
    assert loaded == entries


def test_save_trims_to_max_entries(hist_path):
    entries = [{"idx": i} for i in range(MAX_HISTORY_ENTRIES + 20)]
    save_history(entries, hist_path)
    loaded = load_history(hist_path)
    assert len(loaded) == MAX_HISTORY_ENTRIES
    assert loaded[0]["idx"] == 20


def test_entry_from_result_fields():
    result = _make_result()
    entry = _entry_from_result(result)
    assert entry["project"] == "myapp"
    assert entry["project_type"] == "python"
    assert entry["total"] == 2
    assert entry["outdated"] == 1
    assert "timestamp" in entry
    names = [p["name"] for p in entry["packages"]]
    assert "requests" in names


def test_record_result_appends(hist_path):
    result = _make_result()
    entries = record_result(result, hist_path)
    assert len(entries) == 1
    entries2 = record_result(result, hist_path)
    assert len(entries2) == 2


def test_latest_entry_returns_most_recent(hist_path):
    r1 = _make_result(project="alpha")
    r2 = _make_result(project="beta")
    record_result(r1, hist_path)
    record_result(r2, hist_path)
    record_result(r1, hist_path)
    entry = latest_entry("alpha", hist_path)
    assert entry is not None
    assert entry["project"] == "alpha"


def test_latest_entry_unknown_project(hist_path):
    record_result(_make_result(), hist_path)
    assert latest_entry("unknown", hist_path) is None
