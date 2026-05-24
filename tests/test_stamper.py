"""Tests for depwatch.stamper."""

from __future__ import annotations

import time
from datetime import datetime, timezone

import pytest

from depwatch.checker import CheckResult, PackageStatus
from depwatch.stamper import (
    StampedPackage,
    StampedResult,
    format_stamped,
    stamp_result,
)


def _ps(name: str, current: str, latest: str, outdated: bool) -> PackageStatus:
    return PackageStatus(
        name=name,
        current_version=current,
        latest_version=latest,
        is_outdated=outdated,
    )


def _make_result(outdated: bool = False) -> CheckResult:
    return CheckResult(
        project="myapp",
        project_type="python",
        packages=[
            _ps("requests", "2.28.0", "2.31.0", outdated),
            _ps("flask", "3.0.0", "3.0.0", False),
        ],
    )


def test_stamp_result_returns_stamped_result():
    result = _make_result(outdated=True)
    stamped = stamp_result(result)
    assert isinstance(stamped, StampedResult)
    assert stamped.project == "myapp"
    assert stamped.project_type == "python"


def test_stamp_result_package_count_matches():
    result = _make_result()
    stamped = stamp_result(result)
    assert len(stamped.packages) == 2


def test_stamp_result_stamped_at_is_iso():
    result = _make_result()
    stamped = stamp_result(result)
    # Should parse without error
    dt = datetime.fromisoformat(stamped.stamped_at)
    assert dt.tzinfo is not None


def test_stamp_result_package_has_stamp_field():
    result = _make_result()
    stamped = stamp_result(result)
    for pkg in stamped.packages:
        assert isinstance(pkg, StampedPackage)
        assert pkg.stamp  # non-empty ISO string


def test_stamp_result_age_seconds_non_negative():
    result = _make_result()
    stamped = stamp_result(result)
    for pkg in stamped.packages:
        assert pkg.age_seconds >= 0.0


def test_stamp_result_total_outdated_counts_correctly():
    result = _make_result(outdated=True)
    stamped = stamp_result(result)
    assert stamped.total_outdated == 1


def test_stamped_result_str_contains_project():
    result = _make_result()
    stamped = stamp_result(result)
    assert "myapp" in str(stamped)


def test_stamped_package_str_contains_name():
    result = _make_result(outdated=True)
    stamped = stamp_result(result)
    pkg = stamped.packages[0]
    assert pkg.name in str(pkg)
    assert "outdated" in str(pkg)


def test_format_stamped_includes_all_packages():
    result = _make_result()
    stamped = stamp_result(result)
    text = format_stamped(stamped)
    assert "requests" in text
    assert "flask" in text


def test_format_stamped_empty_packages():
    result = CheckResult(project="empty", project_type="node", packages=[])
    stamped = stamp_result(result)
    text = format_stamped(stamped)
    assert "no packages" in text
