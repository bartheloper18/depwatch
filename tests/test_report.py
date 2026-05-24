"""Tests for depwatch.report."""

import json

import pytest

from depwatch.checker import CheckResult, PackageStatus
from depwatch.report import format_json, format_text, format_report


def _make_result() -> CheckResult:
    return CheckResult(
        project_name="myapp",
        ecosystem="python",
        packages=[
            PackageStatus(name="flask", current_version="2.2.0", latest_version="3.0.0"),
            PackageStatus(name="click", current_version="8.1.3", latest_version="8.1.3"),
        ],
    )


def test_format_text_contains_project_name():
    result = _make_result()
    report = format_text(result)
    assert "myapp" in report


def test_format_text_lists_outdated():
    result = _make_result()
    report = format_text(result)
    assert "flask" in report
    assert "outdated" in report.lower() or "✗" in report


def test_format_text_up_to_date():
    result = CheckResult(
        project_name="cleanapp",
        ecosystem="node",
        packages=[
            PackageStatus(name="lodash", current_version="4.17.21", latest_version="4.17.21"),
        ],
    )
    report = format_text(result)
    assert "up to date" in report.lower() or "✓" in report


def test_format_json_is_valid_json():
    result = _make_result()
    raw = format_json(result)
    data = json.loads(raw)
    assert data["project_name"] == "myapp"
    assert data["ecosystem"] == "python"
    assert isinstance(data["packages"], list)
    assert len(data["packages"]) == 2


def test_format_json_has_checked_at():
    result = _make_result()
    data = json.loads(format_json(result))
    assert "checked_at" in data


def test_format_json_package_fields():
    """Ensure each package entry in the JSON output contains expected fields."""
    result = _make_result()
    data = json.loads(format_json(result))
    for pkg in data["packages"]:
        assert "name" in pkg
        assert "current_version" in pkg
        assert "latest_version" in pkg


def test_format_report_text():
    result = _make_result()
    assert format_report(result, fmt="text") == format_text(result)


def test_format_report_json():
    result = _make_result()
    assert format_report(result, fmt="json") == format_json(result)


def test_format_report_invalid_fmt():
    result = _make_result()
    with pytest.raises(ValueError, match="Unsupported report format"):
        format_report(result, fmt="xml")
