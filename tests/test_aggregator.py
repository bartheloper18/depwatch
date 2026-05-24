"""Unit tests for depwatch.aggregator."""
from __future__ import annotations

import pytest

from depwatch.checker import CheckResult, PackageStatus
from depwatch.aggregator import (
    ProjectAggregate,
    AggregateReport,
    aggregate_results,
    format_aggregate,
)


def _ps(name: str, current: str, latest: str, outdated: bool) -> PackageStatus:
    return PackageStatus(name=name, current=current, latest=latest, is_outdated=outdated)


def _make_result(project: str, pkgs) -> CheckResult:
    return CheckResult(project=project, packages=pkgs)


def test_aggregate_single_all_up_to_date():
    r = _make_result("myapp", [_ps("requests", "2.28.0", "2.28.0", False)])
    report = aggregate_results([r])
    assert report.total_projects == 1
    assert report.total_outdated == 0
    assert report.has_issues is False


def test_aggregate_single_with_outdated():
    r = _make_result(
        "myapp",
        [
            _ps("requests", "2.27.0", "2.28.0", True),
            _ps("flask", "2.0.0", "2.0.0", False),
        ],
    )
    report = aggregate_results([r])
    assert report.total_outdated == 1
    assert report.total_packages == 2
    assert report.has_issues is True


def test_aggregate_multiple_projects():
    r1 = _make_result("app1", [_ps("lodash", "4.17.0", "4.17.21", True)])
    r2 = _make_result("app2", [_ps("express", "4.18.0", "4.18.0", False)])
    report = aggregate_results([r1, r2])
    assert report.total_projects == 2
    assert report.total_outdated == 1
    assert report.total_packages == 2


def test_aggregate_empty_results():
    report = aggregate_results([])
    assert report.total_projects == 0
    assert report.total_outdated == 0
    assert report.has_issues is False


def test_project_aggregate_str():
    pa = ProjectAggregate(project="myapp", total=3, outdated=2, up_to_date=1)
    s = str(pa)
    assert "myapp" in s
    assert "2/3" in s


def test_aggregate_report_str_contains_totals():
    r = _make_result("proj", [_ps("numpy", "1.23.0", "1.24.0", True)])
    report = aggregate_results([r])
    s = str(report)
    assert "1 projects" in s
    assert "1/1" in s


def test_format_aggregate_text():
    r = _make_result("proj", [_ps("numpy", "1.23.0", "1.24.0", True)])
    report = aggregate_results([r])
    out = format_aggregate(report, fmt="text")
    assert "proj" in out


def test_format_aggregate_csv():
    r = _make_result("proj", [_ps("numpy", "1.23.0", "1.24.0", True)])
    report = aggregate_results([r])
    out = format_aggregate(report, fmt="csv")
    lines = out.strip().splitlines()
    assert lines[0] == "project,total,outdated,up_to_date"
    assert "proj,1,1,0" in lines[1]


def test_format_aggregate_csv_up_to_date():
    r = _make_result("proj", [_ps("flask", "2.0", "2.0", False)])
    report = aggregate_results([r])
    out = format_aggregate(report, fmt="csv")
    assert "proj,1,0,1" in out
