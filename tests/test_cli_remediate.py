"""Tests for depwatch.cli_remediate._cmd_remediate."""

import json
import pytest
from pathlib import Path

from depwatch.cli_remediate import _cmd_remediate, _result_from_entry
from depwatch.scanner import ProjectType


class _FakeArgs:
    def __init__(self, config, project=None):
        self.config = config
        self.project = project


def _write_history(path: Path, entries):
    path.write_text(json.dumps(entries))


def _entry(project_name, packages, project_type="python"):
    return {
        "project_name": project_name,
        "project_type": project_type,
        "timestamp": "2024-01-01T00:00:00",
        "packages": packages,
    }


def _pkg(name, current, latest=None, outdated=False):
    return {
        "package": name,
        "current_version": current,
        "latest_version": latest,
        "outdated": outdated,
    }


@pytest.fixture
def project_dir(tmp_path):
    return tmp_path


def test_cmd_remediate_no_history(project_dir, capsys):
    cfg_path = project_dir / "depwatch.json"
    hist_path = project_dir / "history.json"
    cfg_path.write_text(json.dumps({"history_path": str(hist_path)}))
    args = _FakeArgs(config=str(cfg_path))
    rc = _cmd_remediate(args)
    assert rc == 1
    captured = capsys.readouterr()
    assert "No history" in captured.err


def test_cmd_remediate_all_up_to_date(project_dir, capsys):
    hist_path = project_dir / "history.json"
    cfg_path = project_dir / "depwatch.json"
    _write_history(hist_path, [_entry("proj", [_pkg("requests", "2.28.0")])])
    cfg_path.write_text(json.dumps({"history_path": str(hist_path)}))
    args = _FakeArgs(config=str(cfg_path))
    rc = _cmd_remediate(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "up to date" in out.lower()


def test_cmd_remediate_shows_upgrade_command(project_dir, capsys):
    hist_path = project_dir / "history.json"
    cfg_path = project_dir / "depwatch.json"
    _write_history(
        hist_path,
        [_entry("proj", [_pkg("flask", "2.0.0", latest="3.0.0", outdated=True)])],
    )
    cfg_path.write_text(json.dumps({"history_path": str(hist_path)}))
    args = _FakeArgs(config=str(cfg_path))
    rc = _cmd_remediate(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "flask" in out
    assert "pip install" in out


def test_cmd_remediate_unknown_project(project_dir, capsys):
    hist_path = project_dir / "history.json"
    cfg_path = project_dir / "depwatch.json"
    _write_history(hist_path, [_entry("proj", [])])
    cfg_path.write_text(json.dumps({"history_path": str(hist_path)}))
    args = _FakeArgs(config=str(cfg_path), project="nonexistent")
    rc = _cmd_remediate(args)
    assert rc == 1


def test_result_from_entry_reconstructs_correctly():
    entry = _entry(
        "myapp",
        [_pkg("django", "3.2.0", latest="4.2.0", outdated=True)],
        project_type="python",
    )
    result = _result_from_entry(entry)
    assert result.project_name == "myapp"
    assert result.project_type == ProjectType.PYTHON
    assert len(result.packages) == 1
    assert result.packages[0].package == "django"
    assert result.packages[0].outdated is True
