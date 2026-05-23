"""Tests for depwatch.cli_scorer."""
import json
import pytest
from unittest.mock import patch
from depwatch.cli_scorer import _result_from_entry, _format_score, _cmd_scorer
from depwatch.scorer import score_result
from depwatch.checker import CheckResult, PackageStatus


def _entry(project="proj", project_type="python", pkgs=None):
    pkgs = pkgs or []
    return {
        "project": project,
        "project_type": project_type,
        "packages": [
            {"name": p.name, "current": p.current, "latest": p.latest, "is_outdated": p.is_outdated}
            for p in pkgs
        ],
    }


def _pkg(name, current, latest, outdated=True):
    return PackageStatus(name=name, current=current, latest=latest, is_outdated=outdated)


def test_result_from_entry_empty_packages():
    e = _entry()
    r = _result_from_entry(e)
    assert r.project == "proj"
    assert r.packages == []


def test_result_from_entry_with_packages():
    e = _entry(pkgs=[_pkg("flask", "2.0.0", "2.3.0")])
    r = _result_from_entry(e)
    assert len(r.packages) == 1
    assert r.packages[0].name == "flask"


def test_format_score_text():
    result = CheckResult(
        project="myapp", project_type="python",
        packages=[_pkg("requests", "2.0.0", "2.0.0", outdated=False)]
    )
    hs = score_result(result)
    out = _format_score(hs, "text")
    assert "myapp" in out
    assert "requests" in out


def test_format_score_json():
    result = CheckResult(
        project="myapp", project_type="node",
        packages=[_pkg("lodash", "4.0.0", "4.17.0")]
    )
    hs = score_result(result)
    out = _format_score(hs, "json")
    data = json.loads(out)
    assert data["project"] == "myapp"
    assert "grade" in data
    assert len(data["packages"]) == 1


def test_cmd_scorer_no_history(tmp_path, capsys):
    class FakeArgs:
        history = str(tmp_path / "missing.json")
        format = "text"

    with pytest.raises(SystemExit) as exc:
        _cmd_scorer(FakeArgs())
    assert exc.value.code == 1


def test_cmd_scorer_with_history(tmp_path, capsys):
    hist = tmp_path / "hist.json"
    entry = _entry(pkgs=[_pkg("flask", "2.0.0", "3.0.0")])
    hist.write_text(json.dumps([entry]))

    class FakeArgs:
        history = str(hist)
        format = "text"

    _cmd_scorer(FakeArgs())
    captured = capsys.readouterr()
    assert "proj" in captured.out or "flask" in captured.out


def test_cmd_scorer_json_output(tmp_path, capsys):
    hist = tmp_path / "hist.json"
    entry = _entry(pkgs=[_pkg("express", "4.0.0", "4.18.0")])
    hist.write_text(json.dumps([entry]))

    class FakeArgs:
        history = str(hist)
        format = "json"

    _cmd_scorer(FakeArgs())
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "overall" in data
    assert "grade" in data
