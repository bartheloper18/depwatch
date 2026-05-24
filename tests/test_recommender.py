"""Tests for depwatch.recommender"""
from __future__ import annotations

import pytest

from depwatch.checker import CheckResult, PackageStatus
from depwatch.recommender import (
    Recommendation,
    RecommendationReport,
    _priority,
    _reason,
    format_recommendations,
    recommend,
)


def _ps(name: str, current: str, latest: str, outdated: bool) -> PackageStatus:
    return PackageStatus(
        name=name,
        current_version=current,
        latest_version=latest,
        is_outdated=outdated,
    )


def _make_result(packages) -> CheckResult:
    return CheckResult(
        project="myapp",
        project_type="python",
        packages=packages,
    )


# --- _priority ---

def test_priority_major_bump():
    pkg = _ps("django", "2.2.0", "3.0.0", True)
    assert _priority(pkg) == 1


def test_priority_minor_bump():
    pkg = _ps("flask", "1.0.0", "1.1.0", True)
    assert _priority(pkg) == 2


def test_priority_patch_bump():
    pkg = _ps("requests", "2.27.0", "2.27.1", True)
    assert _priority(pkg) == 3


def test_priority_bad_version_defaults_to_2():
    pkg = _ps("weird", "abc", "xyz", True)
    assert _priority(pkg) == 2


# --- _reason ---

def test_reason_priority_1():
    assert "major" in _reason(1)


def test_reason_priority_2():
    assert "minor" in _reason(2)


def test_reason_priority_3():
    assert "patch" in _reason(3)


# --- recommend ---

def test_recommend_skips_up_to_date():
    result = _make_result([_ps("ok", "1.0.0", "1.0.0", False)])
    report = recommend(result)
    assert not report.has_recommendations


def test_recommend_includes_outdated():
    result = _make_result([
        _ps("django", "2.0.0", "3.0.0", True),
        _ps("ok", "1.0.0", "1.0.0", False),
    ])
    report = recommend(result)
    assert report.has_recommendations
    assert len(report.recommendations) == 1
    assert report.recommendations[0].package == "django"


def test_recommend_sorted_by_priority():
    result = _make_result([
        _ps("patch-pkg", "1.0.0", "1.0.1", True),
        _ps("major-pkg", "1.0.0", "2.0.0", True),
        _ps("minor-pkg", "1.0.0", "1.1.0", True),
    ])
    report = recommend(result)
    priorities = [r.priority for r in report.recommendations]
    assert priorities == sorted(priorities)


def test_recommend_project_name_preserved():
    result = _make_result([])
    report = recommend(result)
    assert report.project == "myapp"


# --- format_recommendations ---

def test_format_no_recommendations():
    report = RecommendationReport(project="proj", recommendations=[])
    text = format_recommendations(report)
    assert "no upgrades" in text


def test_format_with_recommendations():
    rec = Recommendation(
        package="flask",
        current="1.0.0",
        latest="2.0.0",
        project_type="python",
        priority=1,
        reason="major version bump – breaking changes likely",
    )
    report = RecommendationReport(project="proj", recommendations=[rec])
    text = format_recommendations(report)
    assert "flask" in text
    assert "P1" in text
    assert "1.0.0" in text
    assert "2.0.0" in text
