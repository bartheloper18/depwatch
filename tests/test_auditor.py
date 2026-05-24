"""Tests for depwatch.auditor"""
from __future__ import annotations

import pytest

from depwatch.auditor import (
    AuditFinding,
    AuditReport,
    _major,
    _severity,
    audit_result,
    format_audit,
)
from depwatch.checker import CheckResult, PackageStatus


def _ps(name: str, current: str, latest: str, outdated: bool = True) -> PackageStatus:
    return PackageStatus(
        name=name,
        current_version=current,
        latest_version=latest,
        is_outdated=outdated,
    )


def _make_result(packages) -> CheckResult:
    return CheckResult(project="myapp", packages=packages)


# ---------------------------------------------------------------------------
# _major
# ---------------------------------------------------------------------------

def test_major_normal():
    assert _major("3.2.1") == 3


def test_major_single_component():
    assert _major("5") == 5


def test_major_invalid_returns_zero():
    assert _major("unknown") == 0


# ---------------------------------------------------------------------------
# _severity
# ---------------------------------------------------------------------------

def test_severity_critical_two_major_gaps():
    pkg = _ps("lib", "1.0.0", "3.0.0")
    assert _severity(pkg) == "critical"


def test_severity_high_one_major_gap():
    pkg = _ps("lib", "2.0.0", "3.0.0")
    assert _severity(pkg) == "high"


def test_severity_low_minor_bump():
    pkg = _ps("lib", "3.1.0", "3.2.0")
    assert _severity(pkg) == "low"


def test_severity_low_patch_bump():
    pkg = _ps("lib", "3.1.0", "3.1.5")
    assert _severity(pkg) == "low"


# ---------------------------------------------------------------------------
# audit_result
# ---------------------------------------------------------------------------

def test_audit_result_empty_when_all_up_to_date():
    result = _make_result([_ps("ok", "1.0.0", "1.0.0", outdated=False)])
    report = audit_result(result)
    assert report.findings == []


def test_audit_result_finds_outdated():
    result = _make_result([_ps("old", "1.0.0", "3.0.0")])
    report = audit_result(result)
    assert len(report.findings) == 1
    assert report.findings[0].severity == "critical"


def test_audit_report_has_critical_true():
    finding = AuditFinding("p", "lib", "1.0", "3.0", "critical")
    report = AuditReport(findings=[finding])
    assert report.has_critical is True


def test_audit_report_has_critical_false():
    finding = AuditFinding("p", "lib", "2.0", "3.0", "high")
    report = AuditReport(findings=[finding])
    assert report.has_critical is False


def test_audit_report_str_clean():
    report = AuditReport(findings=[])
    assert "clean" in str(report)


def test_audit_finding_str_contains_severity():
    f = AuditFinding("proj", "requests", "2.0.0", "3.0.0", "critical")
    assert "CRITICAL" in str(f)
    assert "requests" in str(f)


def test_format_audit_delegates_to_str():
    report = AuditReport(findings=[])
    assert format_audit(report) == str(report)
