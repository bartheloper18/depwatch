"""Tests for depwatch.badge."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from depwatch.badge import (
    BadgeData,
    _choose_color,
    build_badge,
    load_badge,
    save_badge,
)
from depwatch.checker import CheckResult, PackageStatus


def _ps(name: str, outdated: bool) -> PackageStatus:
    return PackageStatus(
        name=name,
        current="1.0.0",
        latest="2.0.0" if outdated else "1.0.0",
        outdated=outdated,
    )


def _make_result(project: str, outdated: int, up_to_date: int) -> CheckResult:
    packages = [_ps(f"pkg-out-{i}", True) for i in range(outdated)]
    packages += [_ps(f"pkg-ok-{i}", False) for i in range(up_to_date)]
    return CheckResult(project_name=project, packages=packages)


def test_choose_color_no_packages():
    assert _choose_color(0, 0) == "lightgrey"


def test_choose_color_all_up_to_date():
    assert _choose_color(0, 5) == "brightgreen"


def test_choose_color_low_ratio():
    assert _choose_color(1, 8) == "yellow"


def test_choose_color_high_ratio():
    assert _choose_color(4, 8) == "red"


def test_build_badge_up_to_date():
    result = _make_result("myapp", outdated=0, up_to_date=3)
    badge = build_badge(result)
    assert badge.label == "myapp"
    assert badge.message == "up to date"
    assert badge.color == "brightgreen"


def test_build_badge_outdated():
    result = _make_result("myapp", outdated=2, up_to_date=8)
    badge = build_badge(result)
    assert "2/10" in badge.message
    assert badge.color == "yellow"


def test_build_badge_no_packages():
    result = _make_result("empty", outdated=0, up_to_date=0)
    badge = build_badge(result)
    assert badge.message == "no packages"
    assert badge.color == "lightgrey"


def test_badge_to_dict_keys():
    badge = BadgeData(label="x", message="ok", color="brightgreen")
    d = badge.to_dict()
    assert set(d.keys()) == {"schemaVersion", "label", "message", "color"}


def test_badge_str():
    badge = BadgeData(label="proj", message="up to date", color="brightgreen")
    assert "proj" in str(badge)
    assert "up to date" in str(badge)


def test_save_and_load_roundtrip(tmp_path: Path):
    badge = BadgeData(label="proj", message="3/10 outdated", color="yellow")
    out = tmp_path / "badge.json"
    save_badge(badge, out)
    loaded = load_badge(out)
    assert loaded.label == badge.label
    assert loaded.message == badge.message
    assert loaded.color == badge.color


def test_save_creates_parent_dirs(tmp_path: Path):
    badge = BadgeData(label="p", message="ok", color="brightgreen")
    out = tmp_path / "nested" / "dir" / "badge.json"
    save_badge(badge, out)
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["label"] == "p"
