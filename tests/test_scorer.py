"""Unit tests for depwatch.scorer."""
import pytest
from depwatch.checker import CheckResult, PackageStatus
from depwatch.scorer import (
    PackageScore,
    HealthScore,
    _score_package,
    score_result,
)


def _ps(name, current, latest, outdated=True):
    return PackageStatus(name=name, current=current, latest=latest, is_outdated=outdated)


def _make_result(pkgs):
    return CheckResult(project="myapp", project_type="python", packages=pkgs)


# --- _score_package ---

def test_score_package_up_to_date():
    ps = _score_package(_ps("requests", "2.28.0", "2.28.0", outdated=False))
    assert ps.score == 1.0
    assert ps.reason == "up-to-date"


def test_score_package_patch_bump():
    ps = _score_package(_ps("flask", "2.2.0", "2.2.5"))
    assert ps.score == pytest.approx(0.8)
    assert "patch" in ps.reason


def test_score_package_minor_bump():
    ps = _score_package(_ps("flask", "2.1.0", "2.3.0"))
    assert ps.score == pytest.approx(0.5)
    assert "minor" in ps.reason


def test_score_package_major_bump():
    ps = _score_package(_ps("django", "3.2.0", "4.0.0"))
    assert ps.score == pytest.approx(0.1)
    assert "major" in ps.reason


def test_score_package_unparseable_version():
    ps = _score_package(_ps("weird", "abc", "xyz"))
    # Still returns a PackageScore; score is low
    assert isinstance(ps, PackageScore)
    assert ps.score <= 0.5


# --- score_result ---

def test_score_result_empty_packages():
    result = _make_result([])
    hs = score_result(result)
    assert hs.overall == pytest.approx(1.0)
    assert hs.grade == "A"
    assert hs.package_scores == []


def test_score_result_all_up_to_date():
    pkgs = [
        _ps("a", "1.0.0", "1.0.0", outdated=False),
        _ps("b", "2.0.0", "2.0.0", outdated=False),
    ]
    hs = score_result(_make_result(pkgs))
    assert hs.overall == pytest.approx(1.0)
    assert hs.grade == "A"


def test_score_result_mixed():
    pkgs = [
        _ps("a", "1.0.0", "1.0.0", outdated=False),  # 1.0
        _ps("b", "1.0.0", "2.0.0"),                   # 0.1
    ]
    hs = score_result(_make_result(pkgs))
    assert hs.overall == pytest.approx(0.55)
    assert hs.grade == "C"


def test_score_result_all_major_bumps():
    pkgs = [
        _ps("a", "1.0.0", "3.0.0"),
        _ps("b", "2.0.0", "5.0.0"),
    ]
    hs = score_result(_make_result(pkgs))
    assert hs.overall == pytest.approx(0.1)
    assert hs.grade == "F"


# --- HealthScore.grade thresholds ---

@pytest.mark.parametrize("score,expected_grade", [
    (1.0, "A"),
    (0.9, "A"),
    (0.75, "B"),
    (0.5, "C"),
    (0.25, "D"),
    (0.0, "F"),
])
def test_grade_thresholds(score, expected_grade):
    hs = HealthScore("p", "python", score, [])
    assert hs.grade == expected_grade


def test_health_score_str():
    hs = HealthScore("myapp", "node", 0.8, [])
    s = str(hs)
    assert "myapp" in s
    assert "node" in s
    assert "0.80" in s
    assert "B" in s
