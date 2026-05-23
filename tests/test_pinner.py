"""Tests for depwatch.pinner."""

from __future__ import annotations

import json
import pathlib

import pytest

from depwatch.checker import CheckResult, PackageStatus
from depwatch.pinner import (
    PinnedSnapshot,
    load_pins,
    pin_result,
    save_pins,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ps(name: str, current: str, latest: str) -> PackageStatus:
    outdated = current != latest
    return PackageStatus(
        name=name,
        current_version=current,
        latest_version=latest,
        outdated=outdated,
    )


def _make_result(packages: list[PackageStatus]) -> CheckResult:
    return CheckResult(
        project="myapp",
        project_type="python",
        packages=packages,
    )


@pytest.fixture()
def pin_path(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path / "pins.json"


# ---------------------------------------------------------------------------
# PinnedSnapshot
# ---------------------------------------------------------------------------

def test_pinned_snapshot_to_dict_round_trips():
    snap = PinnedSnapshot(project="proj", project_type="node", pins={"lodash": "4.17.21"})
    data = snap.to_dict()
    restored = PinnedSnapshot.from_dict(data)
    assert restored.project == "proj"
    assert restored.project_type == "node"
    assert restored.pins == {"lodash": "4.17.21"}


def test_pinned_snapshot_str_contains_package():
    snap = PinnedSnapshot(project="proj", project_type="python", pins={"requests": "2.28.0"})
    text = str(snap)
    assert "requests==2.28.0" in text
    assert "proj" in text


def test_pinned_snapshot_from_dict_defaults():
    snap = PinnedSnapshot.from_dict({})
    assert snap.project == ""
    assert snap.pins == {}


# ---------------------------------------------------------------------------
# pin_result
# ---------------------------------------------------------------------------

def test_pin_result_includes_all_packages():
    pkgs = [_ps("requests", "2.28.0", "2.31.0"), _ps("flask", "2.0.0", "2.0.0")]
    result = _make_result(pkgs)
    snap = pin_result(result)
    assert "requests" in snap.pins
    assert "flask" in snap.pins
    assert snap.pins["requests"] == "2.28.0"


def test_pin_result_outdated_only():
    pkgs = [_ps("requests", "2.28.0", "2.31.0"), _ps("flask", "2.0.0", "2.0.0")]
    result = _make_result(pkgs)
    snap = pin_result(result, outdated_only=True)
    assert "requests" in snap.pins
    assert "flask" not in snap.pins


def test_pin_result_empty_packages():
    result = _make_result([])
    snap = pin_result(result)
    assert snap.pins == {}
    assert snap.project == "myapp"


# ---------------------------------------------------------------------------
# save_pins / load_pins
# ---------------------------------------------------------------------------

def test_save_and_load_round_trips(pin_path):
    snap = PinnedSnapshot(project="app", project_type="python", pins={"numpy": "1.24.0"})
    save_pins(snap, pin_path)
    loaded = load_pins(pin_path)
    assert loaded.project == "app"
    assert loaded.pins == {"numpy": "1.24.0"}


def test_save_creates_file(pin_path):
    snap = PinnedSnapshot(project="app", project_type="python", pins={})
    save_pins(snap, pin_path)
    assert pin_path.exists()


def test_load_missing_file_returns_empty(pin_path):
    snap = load_pins(pin_path)
    assert snap.project == ""
    assert snap.pins == {}


def test_load_malformed_file_returns_empty(pin_path):
    pin_path.write_text("not valid json", encoding="utf-8")
    snap = load_pins(pin_path)
    assert snap.pins == {}
