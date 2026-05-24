"""Tests for depwatch.ranker."""
from __future__ import annotations

import pytest

from depwatch.checker import CheckResult, PackageStatus
from depwatch.ranker import (
    RankedPackage,
    _priority_label,
    _urgency_score,
    format_ranking,
    rank_result,
)


def _ps(name: str, current: str, latest: str, outdated: bool) -> PackageStatus:
    return PackageStatus(
        name=name,
        current_version=current,
        latest_version=latest,
        is_outdated=outdated,
    )


def _make_result(*pkgs: PackageStatus) -> CheckResult:
    return CheckResult(project_name="proj", project_type="python", packages=list(pkgs))


# --- _urgency_score ---

def test_urgency_score_up_to_date_is_zero():
    pkg = _ps("requests", "2.28.0", "2.28.0", False)
    assert _urgency_score(pkg) == 0


def test_urgency_score_major_bump_is_high():
    pkg = _ps("django", "2.2.0", "4.2.0", True)
    score = _urgency_score(pkg)
    assert score >= 70  # 2 major versions → critical territory


def test_urgency_score_minor_bump_is_moderate():
    pkg = _ps("flask", "2.2.0", "2.5.0", True)
    score = _urgency_score(pkg)
    assert 10 <= score < 70


def test_urgency_score_patch_bump_is_low():
    pkg = _ps("click", "8.1.3", "8.1.7", True)
    score = _urgency_score(pkg)
    assert 5 <= score < 40


def test_urgency_score_capped_at_100():
    pkg = _ps("old", "1.0.0", "100.0.0", True)
    assert _urgency_score(pkg) == 100


def test_urgency_score_outdated_minimum_5():
    pkg = _ps("tiny", "1.0.0", "1.0.1", True)
    assert _urgency_score(pkg) >= 5


# --- _priority_label ---

@pytest.mark.parametrize("urgency,expected", [
    (0, "low"),
    (14, "low"),
    (15, "medium"),
    (39, "medium"),
    (40, "high"),
    (69, "high"),
    (70, "critical"),
    (100, "critical"),
])
def test_priority_label_thresholds(urgency, expected):
    assert _priority_label(urgency) == expected


# --- rank_result ---

def test_rank_result_excludes_up_to_date():
    result = _make_result(
        _ps("a", "1.0.0", "1.0.0", False),
        _ps("b", "1.0.0", "2.0.0", True),
    )
    ranked = rank_result(result)
    assert len(ranked) == 1
    assert ranked[0].package.name == "b"


def test_rank_result_sorted_descending():
    result = _make_result(
        _ps("patch", "1.0.0", "1.0.3", True),
        _ps("major", "1.0.0", "3.0.0", True),
        _ps("minor", "1.0.0", "1.3.0", True),
    )
    ranked = rank_result(result)
    urgencies = [r.urgency for r in ranked]
    assert urgencies == sorted(urgencies, reverse=True)


def test_rank_result_empty_when_all_current():
    result = _make_result(_ps("x", "1.0.0", "1.0.0", False))
    assert rank_result(result) == []


def test_ranked_package_str_contains_priority():
    pkg = _ps("lib", "1.0.0", "2.0.0", True)
    rp = RankedPackage(package=pkg, urgency=80, priority="critical")
    assert "CRITICAL" in str(rp)
    assert "lib" in str(rp)


# --- format_ranking ---

def test_format_ranking_all_current():
    result = _make_result(_ps("a", "1.0.0", "1.0.0", False))
    assert format_ranking(rank_result(result)) == "All packages are up-to-date."


def test_format_ranking_lists_packages():
    result = _make_result(
        _ps("alpha", "1.0.0", "2.0.0", True),
        _ps("beta", "1.0.0", "1.1.0", True),
    )
    output = format_ranking(rank_result(result))
    assert "alpha" in output
    assert "beta" in output
    assert "urgency" in output.lower()
