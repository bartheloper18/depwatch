"""Tests for depwatch.sanitizer."""

from __future__ import annotations

import pytest

from depwatch.checker import CheckResult, PackageStatus
from depwatch.sanitizer import (
    SanitizedPackage,
    SanitizedResult,
    _clean,
    sanitize_package,
    sanitize_result,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _ps(name: str, current: str, latest: str, outdated: bool) -> PackageStatus:
    return PackageStatus(
        name=name,
        current_version=current,
        latest_version=latest,
        is_outdated=outdated,
    )


def _make_result(*pkgs: PackageStatus) -> CheckResult:
    return CheckResult(
        project_name="myapp",
        project_type="python",
        packages=list(pkgs),
    )


# ---------------------------------------------------------------------------
# _clean
# ---------------------------------------------------------------------------

def test_clean_strips_caret():
    assert _clean("^1.2.3") == "1.2.3"


def test_clean_strips_tilde():
    assert _clean("~2.0.0") == "2.0.0"


def test_clean_strips_v_prefix():
    assert _clean("v3.1.4") == "3.1.4"


def test_clean_strips_gte():
    assert _clean(">=1.0.0") == "1.0.0"


def test_clean_strips_prerelease_suffix():
    assert _clean("1.2.3-beta.1") == "1.2.3"


def test_clean_strips_build_metadata():
    assert _clean("1.2.3+build.42") == "1.2.3"


def test_clean_plain_version_unchanged():
    assert _clean("4.5.6") == "4.5.6"


def test_clean_empty_string_returns_original():
    # An empty string after stripping prefixes falls back to the original.
    assert _clean("") == ""


# ---------------------------------------------------------------------------
# sanitize_package
# ---------------------------------------------------------------------------

def test_sanitize_package_cleans_versions():
    pkg = _ps("requests", "^2.27.0", "~2.28.1", outdated=True)
    sp = sanitize_package(pkg)
    assert sp.current_version == "2.27.0"
    assert sp.latest_version == "2.28.1"


def test_sanitize_package_preserves_originals():
    pkg = _ps("flask", ">=1.0.0", "2.3.0", outdated=True)
    sp = sanitize_package(pkg)
    assert sp.original_current == ">=1.0.0"
    assert sp.original_latest == "2.3.0"


def test_sanitize_package_str_outdated():
    pkg = _ps("django", "3.2.0", "4.0.0", outdated=True)
    sp = sanitize_package(pkg)
    assert "OUTDATED" in str(sp)


def test_sanitize_package_str_up_to_date():
    pkg = _ps("click", "8.0.0", "8.0.0", outdated=False)
    sp = sanitize_package(pkg)
    assert "ok" in str(sp)


# ---------------------------------------------------------------------------
# sanitize_result
# ---------------------------------------------------------------------------

def test_sanitize_result_project_metadata():
    result = _make_result(_ps("numpy", "1.24.0", "1.25.0", outdated=True))
    sr = sanitize_result(result)
    assert sr.project_name == "myapp"
    assert sr.project_type == "python"


def test_sanitize_result_package_count():
    result = _make_result(
        _ps("numpy", "1.24.0", "1.25.0", outdated=True),
        _ps("pandas", "2.0.0", "2.0.0", outdated=False),
    )
    sr = sanitize_result(result)
    assert len(sr.packages) == 2


def test_sanitize_result_outdated_filter():
    result = _make_result(
        _ps("numpy", "1.24.0", "1.25.0", outdated=True),
        _ps("pandas", "2.0.0", "2.0.0", outdated=False),
    )
    sr = sanitize_result(result)
    assert len(sr.outdated) == 1
    assert sr.outdated[0].name == "numpy"


def test_sanitize_result_str_contains_project():
    result = _make_result(_ps("scipy", "v1.10.0", "1.11.0", outdated=True))
    sr = sanitize_result(result)
    assert "myapp" in str(sr)
