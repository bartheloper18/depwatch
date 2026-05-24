"""Integration tests for the auditor pipeline."""
from __future__ import annotations

import json
import pathlib

import pytest

from depwatch.auditor import audit_result, format_audit
from depwatch.checker import CheckResult, PackageStatus
from depwatch.history import load_history, save_history, record_result


def _ps(name, current, latest, outdated=True):
    return PackageStatus(
        name=name,
        current_version=current,
        latest_version=latest,
        is_outdated=outdated,
    )


def _result(project="app", packages=None):
    return CheckResult(project=project, packages=packages or [])


def test_full_pipeline_critical_finding(tmp_path):
    hist = tmp_path / "h.json"
    result = _result(packages=[_ps("django", "2.0.0", "4.2.0")])
    record_result(str(hist), result)

    entries = load_history(str(hist))
    assert len(entries) == 1

    from depwatch.cli_auditor import _result_from_entry

    loaded = _result_from_entry(entries[0])
    report = audit_result(loaded)
    assert report.has_critical
    output = format_audit(report)
    assert "CRITICAL" in output
    assert "django" in output


def test_full_pipeline_no_findings(tmp_path):
    hist = tmp_path / "h.json"
    result = _result(packages=[_ps("requests", "2.28.0", "2.28.0", outdated=False)])
    record_result(str(hist), result)

    entries = load_history(str(hist))
    from depwatch.cli_auditor import _result_from_entry

    loaded = _result_from_entry(entries[0])
    report = audit_result(loaded)
    assert not report.findings
    assert "clean" in format_audit(report)


def test_full_pipeline_mixed_severities(tmp_path):
    hist = tmp_path / "h.json"
    packages = [
        _ps("lib_a", "1.0.0", "3.0.0"),   # critical
        _ps("lib_b", "2.0.0", "3.0.0"),   # high
        _ps("lib_c", "3.1.0", "3.1.9"),   # low
        _ps("lib_d", "1.0.0", "1.0.0", outdated=False),
    ]
    result = _result(packages=packages)
    record_result(str(hist), result)

    entries = load_history(str(hist))
    from depwatch.cli_auditor import _result_from_entry

    loaded = _result_from_entry(entries[0])
    report = audit_result(loaded)
    assert len(report.findings) == 3
    severities = {f.severity for f in report.findings}
    assert severities == {"critical", "high", "low"}
