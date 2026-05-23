"""Tests for the depwatch.checker module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from depwatch.checker import (
    CheckResult,
    PackageStatus,
    check_node_outdated,
    check_python_outdated,
)


# --- PackageStatus ---

def test_package_status_str_outdated():
    pkg = PackageStatus(name="requests", current_version="2.26.0", latest_version="2.31.0", outdated=True)
    assert "outdated" in str(pkg)
    assert "requests" in str(pkg)


def test_package_status_str_up_to_date():
    pkg = PackageStatus(name="flask", current_version="3.0.0", latest_version="3.0.0", outdated=False)
    assert "up-to-date" in str(pkg)


# --- CheckResult ---

def test_check_result_outdated_packages_filter():
    result = CheckResult(project_path="/fake", ecosystem="python")
    result.packages = [
        PackageStatus(name="a", current_version="1.0", outdated=True),
        PackageStatus(name="b", current_version="2.0", outdated=False),
    ]
    assert len(result.outdated_packages) == 1
    assert result.outdated_packages[0].name == "a"


def test_check_result_has_outdated_false_when_empty():
    result = CheckResult(project_path="/fake", ecosystem="node")
    assert not result.has_outdated


# --- check_python_outdated ---

@patch("depwatch.checker.subprocess.run")
def test_check_python_outdated_success(mock_run):
    fake_output = json.dumps([
        {"name": "requests", "version": "2.26.0", "latest_version": "2.31.0"},
    ])
    mock_run.return_value = MagicMock(returncode=0, stdout=fake_output, stderr="")

    result = check_python_outdated("/fake/project")

    assert result.error is None
    assert len(result.packages) == 1
    assert result.packages[0].name == "requests"
    assert result.packages[0].outdated is True
    assert result.has_outdated


@patch("depwatch.checker.subprocess.run")
def test_check_python_outdated_pip_error(mock_run):
    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="pip error")
    result = check_python_outdated("/fake/project")
    assert result.error == "pip error"
    assert result.packages == []


@patch("depwatch.checker.subprocess.run", side_effect=FileNotFoundError)
def test_check_python_outdated_pip_not_found(mock_run):
    result = check_python_outdated("/fake/project")
    assert result.error == "pip not found"


# --- check_node_outdated ---

@patch("depwatch.checker.subprocess.run")
def test_check_node_outdated_success(mock_run, tmp_path):
    (tmp_path / "package.json").write_text('{"name": "test"}')
    fake_output = json.dumps({
        "lodash": {"current": "4.17.20", "latest": "4.17.21"},
    })
    mock_run.return_value = MagicMock(returncode=1, stdout=fake_output, stderr="")

    result = check_node_outdated(str(tmp_path))

    assert result.error is None
    assert len(result.packages) == 1
    assert result.packages[0].name == "lodash"
    assert result.packages[0].outdated is True


def test_check_node_outdated_missing_package_json(tmp_path):
    result = check_node_outdated(str(tmp_path))
    assert result.error == "package.json not found"


@patch("depwatch.checker.subprocess.run", side_effect=FileNotFoundError)
def test_check_node_outdated_npm_not_found(mock_run, tmp_path):
    (tmp_path / "package.json").write_text('{}')
    result = check_node_outdated(str(tmp_path))
    assert result.error == "npm not found"
