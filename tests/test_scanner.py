"""Tests for depwatch.scanner module."""

import os
import pytest

from depwatch.scanner import (
    ProjectType,
    ProjectScan,
    detect_project_type,
    scan_project,
)


@pytest.fixture
def tmp_project(tmp_path):
    """Return a helper that creates files inside a temp directory."""
    def _create(*filenames):
        for name in filenames:
            (tmp_path / name).write_text("")
        return str(tmp_path)
    return _create


def test_detect_python_requirements(tmp_project):
    directory = tmp_project("requirements.txt")
    assert detect_project_type(directory) == ProjectType.PYTHON


def test_detect_python_pyproject(tmp_project):
    directory = tmp_project("pyproject.toml")
    assert detect_project_type(directory) == ProjectType.PYTHON


def test_detect_node_package_json(tmp_project):
    directory = tmp_project("package.json")
    assert detect_project_type(directory) == ProjectType.NODE


def test_detect_node_takes_priority_when_both_present(tmp_project):
    """If both package.json and requirements.txt exist, Node wins."""
    directory = tmp_project("package.json", "requirements.txt")
    assert detect_project_type(directory) == ProjectType.NODE


def test_detect_unknown_empty_directory(tmp_project):
    directory = tmp_project()
    assert detect_project_type(directory) == ProjectType.UNKNOWN


def test_scan_project_python(tmp_project):
    directory = tmp_project("requirements.txt", "pyproject.toml")
    result = scan_project(directory)
    assert result.project_type == ProjectType.PYTHON
    assert result.is_supported()
    dep_names = [os.path.basename(f) for f in result.dependency_files]
    assert "requirements.txt" in dep_names
    assert "pyproject.toml" in dep_names


def test_scan_project_node(tmp_project):
    directory = tmp_project("package.json")
    result = scan_project(directory)
    assert result.project_type == ProjectType.NODE
    assert result.is_supported()
    assert any(f.endswith("package.json") for f in result.dependency_files)


def test_scan_project_unknown(tmp_project):
    directory = tmp_project()
    result = scan_project(directory)
    assert result.project_type == ProjectType.UNKNOWN
    assert not result.is_supported()
    assert result.dependency_files == []


def test_scan_project_type_override(tmp_project):
    """Explicit project_type override should bypass auto-detection."""
    directory = tmp_project("requirements.txt")
    result = scan_project(directory, project_type="python")
    assert result.project_type == ProjectType.PYTHON


def test_scan_project_invalid_type_override(tmp_project):
    directory = tmp_project("requirements.txt")
    result = scan_project(directory, project_type="ruby")
    assert result.project_type == ProjectType.UNKNOWN
    assert not result.is_supported()


def test_project_scan_path_is_absolute(tmp_project):
    directory = tmp_project("requirements.txt")
    result = scan_project(directory)
    assert os.path.isabs(result.path)
