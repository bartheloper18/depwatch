"""Tests for depwatch.highlighter."""

from __future__ import annotations

import pytest

from depwatch.checker import CheckResult, PackageStatus
from depwatch.highlighter import (
    HighlightedPackage,
    HighlightedResult,
    _highlight_reason,
    _parse_version,
    format_highlights,
    highlight_result,
)


def _ps(name: str, current: str, latest: str, outdated: bool) -> PackageStatus:
    return PackageStatus(name=name, current_version=current, latest_version=latest, is_outdated=outdated)


def _make_result(*pkgs: PackageStatus) -> CheckResult:
    return CheckResult(project="myapp", project_type="python", packages=list(pkgs))


# --- _parse_version ---

def test_parse_version_simple():
    assert _parse_version("1.2.3") == (1, 2, 3)


def test_parse_version_prefix():
    assert _parse_version("^2.0.0") == (2, 0, 0)


def test_parse_version_short():
    assert _parse_version("3.1") == (3, 1, 0)


# --- _highlight_reason ---

def test_highlight_reason_major():
    assert _highlight_reason("1.0.0", "2.0.0") == "major bump"


def test_highlight_reason_minor():
    assert _highlight_reason("1.0.0", "1.3.0") == "minor bump"


def test_highlight_reason_patch():
    assert _highlight_reason("1.0.0", "1.0.5") == "patch bump"


def test_highlight_reason_same():
    assert _highlight_reason("1.2.3", "1.2.3") == ""


# --- highlight_result threshold=major ---

def test_highlight_major_threshold_flags_major():
    result = _make_result(_ps("django", "2.2.0", "3.0.0", True))
    hr = highlight_result(result, threshold="major")
    assert hr.has_stale
    assert hr.stale_packages[0].highlight_reason == "major bump"


def test_highlight_major_threshold_skips_minor():
    result = _make_result(_ps("flask", "1.0.0", "1.1.0", True))
    hr = highlight_result(result, threshold="major")
    assert not hr.has_stale


def test_highlight_minor_threshold_flags_minor():
    result = _make_result(_ps("flask", "1.0.0", "1.1.0", True))
    hr = highlight_result(result, threshold="minor")
    assert hr.has_stale
    assert hr.stale_packages[0].highlight_reason == "minor bump"


def test_highlight_patch_threshold_flags_patch():
    result = _make_result(_ps("requests", "2.27.0", "2.27.1", True))
    hr = highlight_result(result, threshold="patch")
    assert hr.has_stale
    assert hr.stale_packages[0].highlight_reason == "patch bump"


def test_highlight_up_to_date_never_stale():
    result = _make_result(_ps("six", "1.16.0", "1.16.0", False))
    hr = highlight_result(result, threshold="patch")
    assert not hr.has_stale


def test_highlight_result_project_fields():
    result = _make_result()
    hr = highlight_result(result)
    assert hr.project == "myapp"
    assert hr.project_type == "python"


def test_highlighted_package_str_stale():
    pkg = HighlightedPackage("django", "2.2", "3.0", True, True, "major bump")
    assert "major bump" in str(pkg)
    assert "django" in str(pkg)


def test_highlighted_package_str_current():
    pkg = HighlightedPackage("six", "1.16.0", "1.16.0", False, False, "")
    assert "current" in str(pkg)


def test_format_highlights_no_stale():
    result = _make_result(_ps("six", "1.16.0", "1.16.0", False))
    hr = highlight_result(result)
    output = format_highlights(hr)
    assert "No stale packages" in output


def test_format_highlights_with_stale():
    result = _make_result(_ps("django", "2.2.0", "3.0.0", True))
    hr = highlight_result(result, threshold="major")
    output = format_highlights(hr)
    assert "django" in output
    assert "major bump" in output
