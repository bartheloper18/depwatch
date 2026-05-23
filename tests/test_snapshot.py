"""Tests for depwatch/snapshot.py"""
import json
import time
from pathlib import Path

import pytest

from depwatch.checker import CheckResult, PackageStatus
from depwatch.snapshot import (
    Snapshot,
    capture_snapshot,
    diff_snapshots,
    load_snapshot,
    save_snapshot,
)


def _ps(name: str, current: str, latest: str, outdated: bool) -> PackageStatus:
    return PackageStatus(name=name, current_version=current, latest_version=latest, outdated=outdated)


def _make_result(project: str, packages) -> CheckResult:
    return CheckResult(project=project, packages=packages)


# ---------------------------------------------------------------------------
# Snapshot dataclass
# ---------------------------------------------------------------------------

def test_snapshot_to_dict_round_trips():
    snap = Snapshot(timestamp=1_000_000.0, projects={"myapp": [{"name": "requests", "outdated": True}]})
    data = snap.to_dict()
    restored = Snapshot.from_dict(data)
    assert restored.timestamp == snap.timestamp
    assert restored.projects == snap.projects


def test_snapshot_from_dict_defaults():
    snap = Snapshot.from_dict({})
    assert snap.timestamp == 0.0
    assert snap.projects == {}


# ---------------------------------------------------------------------------
# capture_snapshot
# ---------------------------------------------------------------------------

def test_capture_snapshot_basic():
    results = [
        _make_result("proj_a", [_ps("flask", "2.0", "3.0", True)]),
        _make_result("proj_b", [_ps("numpy", "1.24", "1.24", False)]),
    ]
    snap = capture_snapshot(results)
    assert "proj_a" in snap.projects
    assert "proj_b" in snap.projects
    assert snap.projects["proj_a"][0]["name"] == "flask"
    assert snap.projects["proj_a"][0]["outdated"] is True
    assert snap.projects["proj_b"][0]["outdated"] is False
    assert snap.timestamp > 0


def test_capture_snapshot_empty():
    snap = capture_snapshot([])
    assert snap.projects == {}


# ---------------------------------------------------------------------------
# save / load
# ---------------------------------------------------------------------------

def test_save_and_load_roundtrip(tmp_path):
    snap = capture_snapshot([
        _make_result("myapp", [_ps("django", "3.2", "4.2", True)])
    ])
    p = tmp_path / "snap.json"
    save_snapshot(snap, p)
    assert p.exists()
    loaded = load_snapshot(p)
    assert loaded is not None
    assert loaded.projects["myapp"][0]["name"] == "django"


def test_load_snapshot_missing_file(tmp_path):
    result = load_snapshot(tmp_path / "nonexistent.json")
    assert result is None


def test_load_snapshot_malformed_file(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("not valid json{{")
    result = load_snapshot(p)
    assert result is None


# ---------------------------------------------------------------------------
# diff_snapshots
# ---------------------------------------------------------------------------

def test_diff_snapshots_no_change():
    old = Snapshot(timestamp=1.0, projects={"app": [{"name": "pkg", "outdated": True}]})
    new = Snapshot(timestamp=2.0, projects={"app": [{"name": "pkg", "outdated": True}]})
    diff = diff_snapshots(old, new)
    assert diff["became_outdated"] == []
    assert diff["became_current"] == []


def test_diff_snapshots_became_outdated():
    old = Snapshot(timestamp=1.0, projects={"app": [{"name": "pkg", "outdated": False}]})
    new = Snapshot(timestamp=2.0, projects={"app": [{"name": "pkg", "outdated": True}]})
    diff = diff_snapshots(old, new)
    assert "app:pkg" in diff["became_outdated"]
    assert diff["became_current"] == []


def test_diff_snapshots_became_current():
    old = Snapshot(timestamp=1.0, projects={"app": [{"name": "pkg", "outdated": True}]})
    new = Snapshot(timestamp=2.0, projects={"app": [{"name": "pkg", "outdated": False}]})
    diff = diff_snapshots(old, new)
    assert "app:pkg" in diff["became_current"]
    assert diff["became_outdated"] == []


def test_diff_snapshots_new_project():
    old = Snapshot(timestamp=1.0, projects={})
    new = Snapshot(timestamp=2.0, projects={"new_app": [{"name": "lib", "outdated": True}]})
    diff = diff_snapshots(old, new)
    # Package with no prior state should not appear in either list
    assert "new_app:lib" not in diff["became_outdated"]
    assert "new_app:lib" not in diff["became_current"]
