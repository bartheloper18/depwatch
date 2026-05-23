"""Unit tests for depwatch.grouper."""

from __future__ import annotations

import pytest

from depwatch.checker import CheckResult, PackageStatus
from depwatch.grouper import GroupedResult, _severity, group_result, group_results


def _ps(name: str, current: str, latest: str, outdated: bool = True) -> PackageStatus:
    return PackageStatus(
        name=name,
        current_version=current,
        latest_version=latest,
        outdated=outdated,
    )


def _make_result(*pkgs: PackageStatus, name: str = "myproject") -> CheckResult:
    return CheckResult(project_name=name, packages=list(pkgs))


# --- _severity ---

def test_severity_up_to_date():
    pkg = _ps("a", "1.0.0", "1.0.0", outdated=False)
    assert _severity(pkg) == "up_to_date"


def test_severity_critical_major_bump():
    pkg = _ps("a", "1.2.3", "2.0.0")
    assert _severity(pkg) == "critical"


def test_severity_moderate_minor_bump():
    pkg = _ps("a", "1.2.3", "1.5.0")
    assert _severity(pkg) == "moderate"


def test_severity_low_patch_bump():
    pkg = _ps("a", "1.2.3", "1.2.9")
    assert _severity(pkg) == "low"


def test_severity_unparseable_version_returns_low():
    pkg = _ps("a", "unknown", "also-unknown")
    assert _severity(pkg) == "low"


# --- group_result ---

def test_group_result_empty():
    result = _make_result()
    grouped = group_result(result)
    assert isinstance(grouped, GroupedResult)
    assert grouped.total_outdated == 0
    assert grouped.up_to_date == []


def test_group_result_all_up_to_date():
    pkgs = [_ps(f"pkg{i}", "1.0.0", "1.0.0", outdated=False) for i in range(3)]
    grouped = group_result(_make_result(*pkgs))
    assert grouped.total_outdated == 0
    assert len(grouped.up_to_date) == 3


def test_group_result_mixed():
    pkgs = [
        _ps("a", "1.0.0", "2.0.0"),   # critical
        _ps("b", "1.0.0", "1.3.0"),   # moderate
        _ps("c", "1.0.0", "1.0.5"),   # low
        _ps("d", "1.0.0", "1.0.0", outdated=False),  # up_to_date
    ]
    grouped = group_result(_make_result(*pkgs))
    assert len(grouped.critical) == 1
    assert len(grouped.moderate) == 1
    assert len(grouped.low) == 1
    assert len(grouped.up_to_date) == 1
    assert grouped.total_outdated == 3


def test_group_result_project_name():
    result = _make_result(name="special-project")
    grouped = group_result(result)
    assert grouped.project_name == "special-project"


# --- group_results ---

def test_group_results_multiple_projects():
    r1 = _make_result(_ps("a", "1.0", "2.0"), name="proj1")
    r2 = _make_result(_ps("b", "1.0", "1.0", outdated=False), name="proj2")
    mapping = group_results([r1, r2])
    assert set(mapping.keys()) == {"proj1", "proj2"}
    assert mapping["proj1"].total_outdated == 1
    assert mapping["proj2"].total_outdated == 0


def test_group_results_empty_list():
    assert group_results([]) == {}
