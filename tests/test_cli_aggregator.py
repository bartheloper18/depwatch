"""Tests for depwatch.cli_aggregator."""
from __future__ import annotations

import json
import pathlib
import pytest

from depwatch.cli_aggregator import _cmd_aggregator, add_aggregator_subcommand


class _FakeArgs:
    def __init__(self, history: str, fmt: str = "text"):
        self.history = history
        self.fmt = fmt


def _entry(project: str, pkgs):
    return {"project": project, "packages": pkgs}


def _pkg(name, current, latest, outdated):
    return {"name": name, "current": current, "latest": latest, "is_outdated": outdated}


@pytest.fixture()
def hist_path(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path / "history.json"


def test_cmd_aggregator_no_history(hist_path, capsys):
    args = _FakeArgs(history=str(hist_path))
    rc = _cmd_aggregator(args)
    assert rc == 1
    captured = capsys.readouterr()
    assert "No history" in captured.err


def test_cmd_aggregator_text_output(hist_path, capsys):
    entries = [
        _entry("app1", [_pkg("requests", "2.27.0", "2.28.0", True)]),
    ]
    hist_path.write_text(json.dumps(entries))
    args = _FakeArgs(history=str(hist_path), fmt="text")
    rc = _cmd_aggregator(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "app1" in out


def test_cmd_aggregator_csv_output(hist_path, capsys):
    entries = [
        _entry("app1", [_pkg("flask", "2.0", "2.0", False)]),
    ]
    hist_path.write_text(json.dumps(entries))
    args = _FakeArgs(history=str(hist_path), fmt="csv")
    rc = _cmd_aggregator(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "project,total,outdated,up_to_date" in out
    assert "app1" in out


def test_add_aggregator_subcommand_registers():
    import argparse
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_aggregator_subcommand(subs)
    args = parser.parse_args(["aggregate", "some_file.json"])
    assert hasattr(args, "func")
