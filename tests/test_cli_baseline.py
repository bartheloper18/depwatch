"""Tests for depwatch.cli_baseline"""
from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from depwatch.baseline import Baseline
from depwatch.cli_baseline import _cmd_baseline
from depwatch.checker import CheckResult, PackageStatus
from depwatch.scanner import ProjectScan, ProjectType


class _FakeArgs:
    def __init__(self, action, project, bfile):
        self.baseline_action = action
        self.project = project
        self.baseline_file = bfile


def _make_result(project="myapp"):
    return CheckResult(
        project=project,
        packages=[PackageStatus(name="requests", installed="2.28.0", latest="2.31.0")],
    )


def test_clear_removes_file(tmp_path):
    bfile = tmp_path / "baseline.json"
    bfile.write_text(json.dumps({"project": "x", "recorded_at": "", "packages": {}}))
    args = _FakeArgs("clear", str(tmp_path), str(bfile))
    rc = _cmd_baseline(args)
    assert rc == 0
    assert not bfile.exists()


def test_clear_no_file_is_ok(tmp_path):
    args = _FakeArgs("clear", str(tmp_path), str(tmp_path / "nope.json"))
    rc = _cmd_baseline(args)
    assert rc == 0


def test_show_no_baseline_returns_1(tmp_path):
    args = _FakeArgs("show", str(tmp_path), str(tmp_path / "nope.json"))
    rc = _cmd_baseline(args)
    assert rc == 1


def test_show_existing_baseline(tmp_path, capsys):
    bfile = tmp_path / "baseline.json"
    data = {"project": "myapp", "recorded_at": "2024-01-01T00:00:00+00:00",
            "packages": {"requests": "2.28.0"}}
    bfile.write_text(json.dumps(data))
    args = _FakeArgs("show", str(tmp_path), str(bfile))
    rc = _cmd_baseline(args)
    assert rc == 0
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed["project"] == "myapp"


def test_record_unknown_project_returns_1(tmp_path):
    args = _FakeArgs("record", str(tmp_path), str(tmp_path / "b.json"))
    with patch("depwatch.cli_baseline.detect_project_type", return_value=None):
        rc = _cmd_baseline(args)
    assert rc == 1


def test_record_python_project(tmp_path):
    bfile = str(tmp_path / "b.json")
    args = _FakeArgs("record", str(tmp_path), bfile)
    fake_scan = ProjectScan(root=str(tmp_path), project_type=ProjectType.PYTHON, dep_files=[])
    with patch("depwatch.cli_baseline.detect_project_type", return_value=fake_scan), \
         patch("depwatch.cli_baseline.check_python", return_value=_make_result()):
        rc = _cmd_baseline(args)
    assert rc == 0
    assert os.path.exists(bfile)


def test_record_node_project(tmp_path):
    bfile = str(tmp_path / "b.json")
    args = _FakeArgs("record", str(tmp_path), bfile)
    fake_scan = ProjectScan(root=str(tmp_path), project_type=ProjectType.NODE, dep_files=[])
    with patch("depwatch.cli_baseline.detect_project_type", return_value=fake_scan), \
         patch("depwatch.cli_baseline.check_node", return_value=_make_result()):
        rc = _cmd_baseline(args)
    assert rc == 0
