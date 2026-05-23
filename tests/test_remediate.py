"""Unit tests for depwatch.remediate."""

import pytest

from depwatch.checker import CheckResult, PackageStatus
from depwatch.scanner import ProjectType
from depwatch.remediate import (
    RemediationAdvice,
    generate_advice,
    format_advice,
    _upgrade_command,
)


def _ps(package, current, latest=None, outdated=False):
    return PackageStatus(
        package=package,
        current_version=current,
        latest_version=latest,
        outdated=outdated,
    )


def _make_result(project_type=ProjectType.PYTHON, packages=None):
    return CheckResult(
        project_name="myproject",
        project_type=project_type,
        packages=packages or [],
    )


def test_upgrade_command_python():
    cmd = _upgrade_command(ProjectType.PYTHON, "requests", "2.31.0")
    assert cmd == "pip install --upgrade requests==2.31.0"


def test_upgrade_command_node():
    cmd = _upgrade_command(ProjectType.NODE, "lodash", "4.17.21")
    assert cmd == "npm install lodash@4.17.21"


def test_generate_advice_empty_when_all_up_to_date():
    result = _make_result(packages=[_ps("requests", "2.28.0", outdated=False)])
    advice = generate_advice(result)
    assert advice == []


def test_generate_advice_returns_entry_for_outdated():
    result = _make_result(
        packages=[_ps("requests", "2.28.0", latest="2.31.0", outdated=True)]
    )
    advice = generate_advice(result)
    assert len(advice) == 1
    assert advice[0].package == "requests"
    assert advice[0].current_version == "2.28.0"
    assert advice[0].latest_version == "2.31.0"
    assert "pip install" in advice[0].command


def test_generate_advice_skips_missing_latest():
    result = _make_result(
        packages=[_ps("requests", "2.28.0", latest=None, outdated=True)]
    )
    advice = generate_advice(result)
    assert advice == []


def test_generate_advice_node_project():
    result = _make_result(
        project_type=ProjectType.NODE,
        packages=[_ps("lodash", "4.17.0", latest="4.17.21", outdated=True)],
    )
    advice = generate_advice(result)
    assert len(advice) == 1
    assert "npm install" in advice[0].command
    assert "4.17.21" in advice[0].command


def test_format_advice_no_items():
    msg = format_advice([])
    assert "up to date" in msg.lower()


def test_format_advice_lists_commands():
    advice = [
        RemediationAdvice(
            project_name="proj",
            project_type=ProjectType.PYTHON,
            package="flask",
            current_version="2.0.0",
            latest_version="3.0.0",
            command="pip install --upgrade flask==3.0.0",
        )
    ]
    msg = format_advice(advice)
    assert "flask" in msg
    assert "pip install" in msg


def test_remediation_advice_str():
    item = RemediationAdvice(
        project_name="proj",
        project_type=ProjectType.PYTHON,
        package="numpy",
        current_version="1.24.0",
        latest_version="1.26.0",
        command="pip install --upgrade numpy==1.26.0",
    )
    s = str(item)
    assert "numpy" in s
    assert "1.24.0" in s
    assert "1.26.0" in s
