"""Tests for depwatch.suppressor."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from depwatch.checker import CheckResult, PackageStatus
from depwatch.scanner import ProjectType
from depwatch.suppressor import (
    Suppression,
    add_suppression,
    filter_suppressed,
    is_suppressed,
    load_suppressions,
    remove_suppression,
    save_suppressions,
)


@pytest.fixture()
def sup_path(tmp_path: Path) -> Path:
    return tmp_path / "suppressions.json"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _ps(name: str, current: str, latest: str) -> PackageStatus:
    return PackageStatus(name=name, current_version=current, latest_version=latest)


def _make_result(*pkgs: PackageStatus) -> CheckResult:
    return CheckResult(project="myapp", project_type=ProjectType.PYTHON, packages=list(pkgs))


# ---------------------------------------------------------------------------
# Suppression.is_active
# ---------------------------------------------------------------------------

def test_is_active_indefinite():
    s = Suppression(package="requests", project="myapp", expires_at=None)
    assert s.is_active() is True


def test_is_active_future_expiry():
    s = Suppression(package="requests", project="myapp", expires_at=_now() + timedelta(hours=1))
    assert s.is_active() is True


def test_is_active_past_expiry():
    s = Suppression(package="requests", project="myapp", expires_at=_now() - timedelta(seconds=1))
    assert s.is_active() is False


def test_suppression_str_contains_package():
    s = Suppression(package="flask", project="api", expires_at=None)
    assert "flask" in str(s)
    assert "indefinite" in str(s)


# ---------------------------------------------------------------------------
# load / save round-trip
# ---------------------------------------------------------------------------

def test_load_missing_file(sup_path: Path):
    assert load_suppressions(sup_path) == []


def test_load_malformed_file(sup_path: Path):
    sup_path.write_text("not json")
    assert load_suppressions(sup_path) == []


def test_save_and_load_roundtrip(sup_path: Path):
    s = Suppression(package="django", project="web", expires_at=_now() + timedelta(days=7), reason="known")
    save_suppressions([s], sup_path)
    loaded = load_suppressions(sup_path)
    assert len(loaded) == 1
    assert loaded[0].package == "django"
    assert loaded[0].reason == "known"
    assert loaded[0].expires_at is not None


# ---------------------------------------------------------------------------
# add / remove helpers
# ---------------------------------------------------------------------------

def test_add_suppression_new_entry():
    result = add_suppression([], "requests", "myapp")
    assert len(result) == 1
    assert result[0].package == "requests"


def test_add_suppression_replaces_existing():
    existing = [Suppression(package="requests", project="myapp", expires_at=None)]
    updated = add_suppression(existing, "requests", "myapp", expires_at=_now() + timedelta(hours=1))
    assert len(updated) == 1
    assert updated[0].expires_at is not None


def test_remove_suppression():
    sups = [Suppression(package="requests", project="myapp", expires_at=None)]
    result = remove_suppression(sups, "requests", "myapp")
    assert result == []


# ---------------------------------------------------------------------------
# is_suppressed
# ---------------------------------------------------------------------------

def test_is_suppressed_active():
    sups = [Suppression(package="requests", project="myapp", expires_at=None)]
    assert is_suppressed(sups, "requests", "myapp") is True


def test_is_suppressed_expired():
    sups = [Suppression(package="requests", project="myapp", expires_at=_now() - timedelta(seconds=1))]
    assert is_suppressed(sups, "requests", "myapp") is False


def test_is_suppressed_unknown_package():
    assert is_suppressed([], "unknown", "myapp") is False


# ---------------------------------------------------------------------------
# filter_suppressed
# ---------------------------------------------------------------------------

def test_filter_suppressed_removes_outdated_suppressed_package():
    pkgs = [_ps("requests", "2.0.0", "3.0.0"), _ps("flask", "1.0.0", "2.0.0")]
    result = _make_result(*pkgs)
    sups = [Suppression(package="requests", project="myapp", expires_at=None)]
    filtered = filter_suppressed(result, sups)
    names = [p.name for p in filtered.packages]
    assert "requests" not in names
    assert "flask" in names


def test_filter_suppressed_keeps_up_to_date_suppressed_package():
    pkgs = [_ps("requests", "3.0.0", "3.0.0")]
    result = _make_result(*pkgs)
    sups = [Suppression(package="requests", project="myapp", expires_at=None)]
    filtered = filter_suppressed(result, sups)
    assert len(filtered.packages) == 1


def test_filter_suppressed_no_suppressions_unchanged():
    pkgs = [_ps("requests", "2.0.0", "3.0.0")]
    result = _make_result(*pkgs)
    filtered = filter_suppressed(result, [])
    assert len(filtered.packages) == 1
