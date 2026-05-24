"""Tests for depwatch.classifier."""
from __future__ import annotations

import pytest

from depwatch.checker import CheckResult, PackageStatus
from depwatch.classifier import (
    ClassificationReport,
    ClassifiedPackage,
    _detect_category,
    classify_result,
    format_classification,
)


def _ps(name: str, current: str, latest: str, outdated: bool) -> PackageStatus:
    return PackageStatus(
        name=name,
        current_version=current,
        latest_version=latest,
        is_outdated=outdated,
    )


def _make_result(*pkgs: PackageStatus) -> CheckResult:
    return CheckResult(
        project="myproject",
        project_type="python",
        packages=list(pkgs),
    )


def test_detect_category_current():
    pkg = _ps("requests", "2.28.0", "2.28.0", False)
    assert _detect_category(pkg) == "current"


def test_detect_category_patch():
    pkg = _ps("requests", "2.28.0", "2.28.1", True)
    assert _detect_category(pkg) == "patch"


def test_detect_category_minor():
    pkg = _ps("requests", "2.28.0", "2.29.0", True)
    assert _detect_category(pkg) == "minor"


def test_detect_category_major():
    pkg = _ps("requests", "2.28.0", "3.0.0", True)
    assert _detect_category(pkg) == "major"


def test_detect_category_bad_version_returns_unknown():
    pkg = _ps("weird", "abc", "xyz", True)
    assert _detect_category(pkg) == "unknown"


def test_classify_result_all_current():
    result = _make_result(_ps("flask", "2.0.0", "2.0.0", False))
    report = classify_result(result)
    assert len(report.packages) == 1
    assert report.packages[0].category == "current"
    assert not report.has_security


def test_classify_result_security_flag():
    result = _make_result(_ps("pillow", "9.0.0", "9.1.0", True))
    report = classify_result(result, security_packages=["pillow"])
    assert report.packages[0].category == "security"
    assert report.has_security


def test_classify_result_mixed():
    result = _make_result(
        _ps("flask", "2.0.0", "2.0.0", False),
        _ps("numpy", "1.23.0", "1.24.0", True),
        _ps("django", "3.2.0", "4.0.0", True),
    )
    report = classify_result(result)
    cats = {p.name: p.category for p in report.packages}
    assert cats["flask"] == "current"
    assert cats["numpy"] == "minor"
    assert cats["django"] == "major"


def test_by_category_groups_correctly():
    result = _make_result(
        _ps("a", "1.0.0", "2.0.0", True),
        _ps("b", "1.0.0", "1.1.0", True),
        _ps("c", "1.0.0", "1.0.0", False),
    )
    report = classify_result(result)
    by_cat = report.by_category
    assert len(by_cat["major"]) == 1
    assert len(by_cat["minor"]) == 1
    assert len(by_cat["current"]) == 1


def test_format_classification_no_packages():
    report = ClassificationReport(project="empty", packages=[])
    text = format_classification(report)
    assert "no packages" in text


def test_format_classification_shows_project():
    result = _make_result(_ps("requests", "2.0.0", "3.0.0", True))
    report = classify_result(result)
    text = format_classification(report)
    assert "myproject" in text


def test_classified_package_str():
    pkg = ClassifiedPackage(
        name="flask",
        current_version="2.0.0",
        latest_version="3.0.0",
        category="major",
        project_type="python",
    )
    assert "flask" in str(pkg)
    assert "major" in str(pkg)
