"""Unit tests for depwatch.filterer."""
import pytest
from depwatch.checker import CheckResult, PackageStatus
from depwatch.filterer import FilterCriteria, filter_result, format_filtered, _bump_level


def _ps(name, cur, lat, outdated):
    return PackageStatus(name=name, current_version=cur,
                         latest_version=lat, is_outdated=outdated)


def _make_result(packages):
    return CheckResult(
        project_name="myapp",
        project_type="python",
        packages=packages,
        checked_at="2024-01-01T00:00:00",
    )


def test_bump_level_up_to_date():
    pkg = _ps("a", "1.0.0", "1.0.0", False)
    assert _bump_level(pkg) == 0


def test_bump_level_patch():
    pkg = _ps("a", "1.0.0", "1.0.1", True)
    assert _bump_level(pkg) == 1


def test_bump_level_minor():
    pkg = _ps("a", "1.0.0", "1.2.0", True)
    assert _bump_level(pkg) == 2


def test_bump_level_major():
    pkg = _ps("a", "1.0.0", "2.0.0", True)
    assert _bump_level(pkg) == 3


def test_filter_only_outdated():
    pkgs = [_ps("a", "1.0", "2.0", True), _ps("b", "1.0", "1.0", False)]
    result = _make_result(pkgs)
    criteria = FilterCriteria(only_outdated=True)
    filtered = filter_result(result, criteria)
    assert len(filtered.packages) == 1
    assert filtered.packages[0].name == "a"


def test_filter_name_contains():
    pkgs = [_ps("requests", "2.0", "3.0", True), _ps("flask", "1.0", "2.0", True)]
    result = _make_result(pkgs)
    criteria = FilterCriteria(name_contains="req")
    filtered = filter_result(result, criteria)
    assert len(filtered.packages) == 1
    assert filtered.packages[0].name == "requests"


def test_filter_min_bump_minor_excludes_patch():
    pkgs = [_ps("a", "1.0.0", "1.0.1", True), _ps("b", "1.0.0", "1.1.0", True)]
    result = _make_result(pkgs)
    criteria = FilterCriteria(min_bump="minor")
    filtered = filter_result(result, criteria)
    assert len(filtered.packages) == 1
    assert filtered.packages[0].name == "b"


def test_filter_min_bump_major_only():
    pkgs = [
        _ps("a", "1.0.0", "1.0.1", True),
        _ps("b", "1.0.0", "1.1.0", True),
        _ps("c", "1.0.0", "2.0.0", True),
    ]
    result = _make_result(pkgs)
    criteria = FilterCriteria(min_bump="major")
    filtered = filter_result(result, criteria)
    assert len(filtered.packages) == 1
    assert filtered.packages[0].name == "c"


def test_filter_project_type_mismatch_returns_empty():
    pkgs = [_ps("a", "1.0", "2.0", True)]
    result = _make_result(pkgs)
    criteria = FilterCriteria(project_types=["node"])
    filtered = filter_result(result, criteria)
    assert filtered.packages == []


def test_filter_project_type_match_keeps_packages():
    pkgs = [_ps("a", "1.0", "2.0", True)]
    result = _make_result(pkgs)
    criteria = FilterCriteria(project_types=["python"])
    filtered = filter_result(result, criteria)
    assert len(filtered.packages) == 1


def test_format_filtered_empty():
    result = _make_result([])
    msg = format_filtered(result)
    assert "No packages match" in msg


def test_format_filtered_with_packages():
    pkgs = [_ps("requests", "2.0", "3.0", True)]
    result = _make_result(pkgs)
    msg = format_filtered(result)
    assert "requests" in msg
    assert "myapp" in msg
