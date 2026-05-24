"""Tests for depwatch.normalizer."""
import pytest
from depwatch.checker import CheckResult, PackageStatus
from depwatch.normalizer import (
    NormalizedPackage,
    NormalizedResult,
    _parse_version,
    normalize_package,
    normalize_result,
)


def _ps(name: str, current: str, latest: str, outdated: bool) -> PackageStatus:
    return PackageStatus(
        name=name,
        current_version=current,
        latest_version=latest,
        is_outdated=outdated,
    )


def _make_result(*pkgs: PackageStatus) -> CheckResult:
    return CheckResult(project="myproject", packages=list(pkgs))


# --- _parse_version ---

def test_parse_version_simple():
    assert _parse_version("1.2.3") == [1, 2, 3]


def test_parse_version_prefix():
    assert _parse_version("v2.0.1") == [2, 0, 1]


def test_parse_version_single():
    assert _parse_version("3") == [3]


def test_parse_version_non_numeric_fallback():
    assert _parse_version("unknown") == [0]


def test_parse_version_with_whitespace():
    assert _parse_version("  1.4.0  ") == [1, 4, 0]


# --- normalize_package ---

def test_normalize_package_outdated():
    pkg = _ps("requests", "2.0.0", "2.28.0", True)
    np = normalize_package(pkg)
    assert np.name == "requests"
    assert np.current_parts == [2, 0, 0]
    assert np.latest_parts == [2, 28, 0]
    assert np.is_outdated is True


def test_normalize_package_up_to_date():
    pkg = _ps("flask", "2.3.1", "2.3.1", False)
    np = normalize_package(pkg)
    assert np.is_outdated is False
    assert np.current_parts == np.latest_parts


def test_normalize_package_str_contains_name():
    pkg = _ps("numpy", "1.23.0", "1.25.0", True)
    np = normalize_package(pkg)
    assert "numpy" in str(np)
    assert "outdated" in str(np)


# --- normalize_result ---

def test_normalize_result_project_name():
    result = _make_result(_ps("a", "1.0.0", "1.0.0", False))
    nr = normalize_result(result)
    assert nr.project == "myproject"


def test_normalize_result_outdated_filter():
    result = _make_result(
        _ps("a", "1.0.0", "2.0.0", True),
        _ps("b", "3.0.0", "3.0.0", False),
    )
    nr = normalize_result(result)
    assert len(nr.packages) == 2
    assert len(nr.outdated()) == 1
    assert nr.outdated()[0].name == "a"


def test_normalize_result_str_contains_project():
    result = _make_result(_ps("x", "0.1.0", "0.2.0", True))
    nr = normalize_result(result)
    assert "myproject" in str(nr)


def test_normalize_result_empty_packages():
    result = CheckResult(project="empty", packages=[])
    nr = normalize_result(result)
    assert nr.packages == []
    assert nr.outdated() == []
