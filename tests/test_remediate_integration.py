"""Integration tests: remediation advice round-trip through history."""

import json
from pathlib import Path

import pytest

from depwatch.checker import CheckResult, PackageStatus
from depwatch.history import record_result, load_history, latest_entry
from depwatch.scanner import ProjectType
from depwatch.remediate import generate_advice, format_advice
from depwatch.cli_remediate import _result_from_entry


def _ps(package, current, latest=None, outdated=False):
    return PackageStatus(
        package=package,
        current_version=current,
        latest_version=latest,
        outdated=outdated,
    )


@pytest.fixture
def hist_file(tmp_path):
    return tmp_path / "history.json"


def test_roundtrip_advice_python(hist_file):
    result = CheckResult(
        project_name="backend",
        project_type=ProjectType.PYTHON,
        packages=[
            _ps("requests", "2.28.0", latest="2.31.0", outdated=True),
            _ps("flask", "2.3.0", latest="2.3.0", outdated=False),
        ],
    )
    record_result(hist_file, result)
    history = load_history(hist_file)
    entry = latest_entry(history, "backend")
    assert entry is not None
    rebuilt = _result_from_entry(entry)
    advice = generate_advice(rebuilt)
    assert len(advice) == 1
    assert advice[0].package == "requests"
    assert "pip install" in advice[0].command


def test_roundtrip_advice_node(hist_file):
    result = CheckResult(
        project_name="frontend",
        project_type=ProjectType.NODE,
        packages=[
            _ps("lodash", "4.17.0", latest="4.17.21", outdated=True),
        ],
    )
    record_result(hist_file, result)
    history = load_history(hist_file)
    entry = latest_entry(history, "frontend")
    rebuilt = _result_from_entry(entry)
    advice = generate_advice(rebuilt)
    assert len(advice) == 1
    assert "npm install" in advice[0].command
    assert "4.17.21" in advice[0].command


def test_no_advice_when_all_current(hist_file):
    result = CheckResult(
        project_name="service",
        project_type=ProjectType.PYTHON,
        packages=[_ps("boto3", "1.28.0", latest="1.28.0", outdated=False)],
    )
    record_result(hist_file, result)
    history = load_history(hist_file)
    entry = latest_entry(history, "service")
    rebuilt = _result_from_entry(entry)
    advice = generate_advice(rebuilt)
    assert advice == []
    msg = format_advice(advice)
    assert "up to date" in msg.lower()
