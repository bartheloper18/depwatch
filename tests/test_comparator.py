"""Tests for depwatch.comparator."""
import pytest

from depwatch.checker import CheckResult, PackageStatus
from depwatch.comparator import (
    ComparisonReport,
    PackageChange,
    compare_results,
)


def _ps(name: str, project: str, current: str, latest: str, outdated: bool) -> PackageStatus:
    return PackageStatus(
        name=name,
        project=project,
        current_version=current,
        latest_version=latest,
        outdated=outdated,
    )


def _result(*packages: PackageStatus) -> CheckResult:
    return CheckResult(packages=list(packages))


# ---------------------------------------------------------------------------
# PackageChange.__str__
# ---------------------------------------------------------------------------

def test_package_change_str_became_outdated():
    c = PackageChange("requests", "myapp", "2.0", "2.1", False, True)
    assert "became outdated" in str(c)


def test_package_change_str_resolved():
    c = PackageChange("requests", "myapp", "2.0", "2.1", True, False)
    assert "resolved" in str(c)


def test_package_change_str_version_changed_still_outdated():
    c = PackageChange("requests", "myapp", "2.0", "2.1", True, True)
    assert "still outdated" in str(c)


def test_package_change_str_unchanged():
    c = PackageChange("requests", "myapp", "2.0", "2.0", False, False)
    assert "unchanged" in str(c)


# ---------------------------------------------------------------------------
# ComparisonReport helpers
# ---------------------------------------------------------------------------

def test_comparison_report_has_changes_false_when_empty():
    report = ComparisonReport()
    assert not report.has_changes


def test_comparison_report_has_changes_true_when_newly_outdated():
    c = PackageChange("x", "p", "1", "2", False, True)
    report = ComparisonReport(newly_outdated=[c])
    assert report.has_changes


def test_comparison_report_str_no_changes():
    assert str(ComparisonReport()) == "No changes detected."


def test_comparison_report_str_lists_sections():
    c = PackageChange("x", "p", "1", "2", False, True)
    report = ComparisonReport(newly_outdated=[c])
    text = str(report)
    assert "Newly outdated" in text
    assert "x" in text


# ---------------------------------------------------------------------------
# compare_results
# ---------------------------------------------------------------------------

def test_compare_no_change():
    pkg = _ps("flask", "app", "2.0", "2.0", False)
    before = _result(pkg)
    after = _result(pkg)
    report = compare_results(before, after)
    assert not report.has_changes


def test_compare_newly_outdated():
    before = _result(_ps("flask", "app", "2.0", "2.0", False))
    after = _result(_ps("flask", "app", "2.0", "3.0", True))
    report = compare_results(before, after)
    assert len(report.newly_outdated) == 1
    assert report.newly_outdated[0].name == "flask"
    assert not report.resolved
    assert not report.version_changed


def test_compare_resolved():
    before = _result(_ps("flask", "app", "2.0", "3.0", True))
    after = _result(_ps("flask", "app", "3.0", "3.0", False))
    report = compare_results(before, after)
    assert len(report.resolved) == 1
    assert not report.newly_outdated


def test_compare_version_changed_still_outdated():
    before = _result(_ps("flask", "app", "2.0", "3.0", True))
    after = _result(_ps("flask", "app", "2.1", "3.0", True))
    report = compare_results(before, after)
    assert len(report.version_changed) == 1
    assert report.version_changed[0].old_version == "2.0"
    assert report.version_changed[0].new_version == "2.1"


def test_compare_multiple_projects():
    before = _result(
        _ps("requests", "api", "2.0", "2.0", False),
        _ps("lodash", "web", "4.0", "4.17", True),
    )
    after = _result(
        _ps("requests", "api", "2.0", "3.0", True),
        _ps("lodash", "web", "4.17", "4.17", False),
    )
    report = compare_results(before, after)
    assert len(report.newly_outdated) == 1
    assert len(report.resolved) == 1
    assert report.newly_outdated[0].name == "requests"
    assert report.resolved[0].name == "lodash"
