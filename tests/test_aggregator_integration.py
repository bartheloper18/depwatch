"""Integration tests: aggregate_results + format_aggregate end-to-end."""
from __future__ import annotations

import json
import pathlib

import pytest

from depwatch.checker import CheckResult, PackageStatus
from depwatch.aggregator import aggregate_results, format_aggregate


def _ps(name, current, latest, outdated):
    return PackageStatus(name=name, current=current, latest=latest, is_outdated=outdated)


def _result(project, pkgs):
    return CheckResult(project=project, packages=pkgs)


def test_full_pipeline_mixed_projects():
    results = [
        _result("backend", [_ps("django", "3.2.0", "4.0.0", True), _ps("celery", "5.2", "5.2", False)]),
        _result("frontend", [_ps("react", "17.0.0", "18.0.0", True), _ps("lodash", "4.17.21", "4.17.21", False)]),
    ]
    report = aggregate_results(results)
    assert report.total_projects == 2
    assert report.total_outdated == 2
    assert report.total_packages == 4
    assert report.has_issues is True


def test_full_pipeline_all_current():
    results = [
        _result("api", [_ps("fastapi", "0.95.0", "0.95.0", False)]),
        _result("worker", [_ps("rq", "1.15.0", "1.15.0", False)]),
    ]
    report = aggregate_results(results)
    assert report.has_issues is False
    text = format_aggregate(report)
    assert "0/2" in text


def test_csv_roundtrip_parseable():
    results = [
        _result("svc", [_ps("httpx", "0.23.0", "0.24.0", True)]),
    ]
    report = aggregate_results(results)
    csv_out = format_aggregate(report, fmt="csv")
    lines = csv_out.strip().splitlines()
    header = lines[0].split(",")
    assert header == ["project", "total", "outdated", "up_to_date"]
    row = lines[1].split(",")
    assert row[0] == "svc"
    assert int(row[1]) == 1
    assert int(row[2]) == 1
    assert int(row[3]) == 0
