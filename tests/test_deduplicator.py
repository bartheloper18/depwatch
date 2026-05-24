"""Tests for depwatch.deduplicator."""
from __future__ import annotations

import pytest

from depwatch.checker import CheckResult, PackageStatus
from depwatch.scanner import ProjectType
from depwatch.deduplicator import (
    deduplicate_results,
    format_deduplicated,
    DeduplicatedReport,
)


def _ps(name: str, current: str, latest: str, outdated: bool) -> PackageStatus:
    return PackageStatus(
        name=name,
        current_version=current,
        latest_version=latest,
        is_outdated=outdated,
    )


def _make_result(project: str, packages: list[PackageStatus]) -> CheckResult:
    return CheckResult(
        project_name=project,
        project_type=ProjectType.PYTHON,
        packages=packages,
    )


def test_deduplicate_empty_list():
    report = deduplicate_results([])
    assert report.total_packages == 0
    assert report.total_outdated == 0
    assert not report.has_issues


def test_deduplicate_single_result_no_overlap():
    result = _make_result("proj-a", [
        _ps("requests", "2.28.0", "2.31.0", True),
        _ps("flask", "2.0.0", "2.0.0", False),
    ])
    report = deduplicate_results([result])
    assert report.total_packages == 2
    assert report.total_outdated == 1
    assert report.has_issues


def test_deduplicate_two_results_no_overlap():
    r1 = _make_result("proj-a", [_ps("requests", "2.28.0", "2.31.0", True)])
    r2 = _make_result("proj-b", [_ps("flask", "2.0.0", "2.0.0", False)])
    report = deduplicate_results([r1, r2])
    assert report.total_packages == 2


def test_deduplicate_same_package_same_version():
    pkg = _ps("requests", "2.28.0", "2.31.0", True)
    r1 = _make_result("proj-a", [pkg])
    r2 = _make_result("proj-b", [pkg])
    report = deduplicate_results([r1, r2])
    assert report.total_packages == 1
    deduped = report.packages[0]
    assert set(deduped.seen_in) == {"proj-a", "proj-b"}


def test_deduplicate_higher_latest_version_wins():
    r1 = _make_result("proj-a", [_ps("requests", "2.28.0", "2.30.0", True)])
    r2 = _make_result("proj-b", [_ps("requests", "2.28.0", "2.31.0", True)])
    report = deduplicate_results([r1, r2])
    assert report.total_packages == 1
    assert report.packages[0].latest_version == "2.31.0"


def test_deduplicate_case_insensitive_name():
    r1 = _make_result("proj-a", [_ps("Requests", "2.28.0", "2.31.0", True)])
    r2 = _make_result("proj-b", [_ps("requests", "2.28.0", "2.31.0", True)])
    report = deduplicate_results([r1, r2])
    assert report.total_packages == 1


def test_deduplicate_seen_in_no_duplicates():
    pkg = _ps("flask", "2.0.0", "2.0.0", False)
    r1 = _make_result("proj-a", [pkg])
    r2 = _make_result("proj-a", [pkg])
    report = deduplicate_results([r1, r2])
    assert report.packages[0].seen_in.count("proj-a") == 1


def test_format_deduplicated_empty():
    report = DeduplicatedReport(packages=[])
    text = format_deduplicated(report)
    assert "No packages" in text


def test_format_deduplicated_non_empty():
    r = _make_result("proj-a", [_ps("requests", "2.28.0", "2.31.0", True)])
    report = deduplicate_results([r])
    text = format_deduplicated(report)
    assert "requests" in text
    assert "outdated" in text


def test_deduplicatedpackage_str():
    r = _make_result("proj-a", [_ps("flask", "2.0.0", "2.0.0", False)])
    report = deduplicate_results([r])
    s = str(report.packages[0])
    assert "flask" in s
    assert "up-to-date" in s
    assert "proj-a" in s
