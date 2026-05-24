"""Tests for depwatch.merger and depwatch.cli_merger."""
import json
import pytest
from pathlib import Path

from depwatch.checker import CheckResult, PackageStatus
from depwatch.merger import merge_results, format_merged, MergedReport


def _ps(name: str, current: str, latest: str, outdated: bool) -> PackageStatus:
    return PackageStatus(name=name, current=current, latest=latest, outdated=outdated)


def _make_result(project: str, pkgs) -> CheckResult:
    return CheckResult(project_name=project, packages=pkgs)


# ── MergedReport properties ────────────────────────────────────────────────

def test_merge_empty_list():
    report = merge_results([])
    assert report.total_projects == 0
    assert report.total_packages == 0
    assert report.total_outdated == 0
    assert report.projects_with_issues == []


def test_merge_single_all_up_to_date():
    r = _make_result("alpha", [_ps("requests", "2.28.0", "2.28.0", False)])
    report = merge_results([r])
    assert report.total_projects == 1
    assert report.total_packages == 1
    assert report.total_outdated == 0
    assert report.projects_with_issues == []


def test_merge_single_with_outdated():
    r = _make_result("beta", [_ps("flask", "2.0.0", "3.0.0", True)])
    report = merge_results([r])
    assert report.total_outdated == 1
    assert "beta" in report.projects_with_issues


def test_merge_multiple_projects():
    r1 = _make_result("proj-a", [_ps("numpy", "1.24", "1.25", True)])
    r2 = _make_result("proj-b", [_ps("pandas", "2.0", "2.0", False)])
    report = merge_results([r1, r2])
    assert report.total_projects == 2
    assert report.total_packages == 2
    assert report.total_outdated == 1
    assert report.projects_with_issues == ["proj-a"]


def test_packages_by_project_keys():
    r1 = _make_result("x", [_ps("a", "1", "2", True)])
    r2 = _make_result("y", [_ps("b", "1", "1", False)])
    report = merge_results([r1, r2])
    by_proj = report.packages_by_project()
    assert set(by_proj.keys()) == {"x", "y"}


# ── format_merged ──────────────────────────────────────────────────────────

def test_format_merged_text_up_to_date():
    r = _make_result("clean", [_ps("lib", "1.0", "1.0", False)])
    out = format_merged(merge_results([r]))
    assert "All projects up to date" in out
    assert "clean" not in out or "All" in out


def test_format_merged_text_lists_issues():
    r = _make_result("dirty", [_ps("old", "1.0", "2.0", True)])
    out = format_merged(merge_results([r]))
    assert "dirty" in out


def test_format_merged_csv_header():
    r = _make_result("p", [_ps("q", "1", "1", False)])
    out = format_merged(merge_results([r]), fmt="csv")
    assert out.startswith("project,total,outdated")


def test_format_merged_csv_row_values():
    r = _make_result("myapp", [
        _ps("a", "1", "2", True),
        _ps("b", "1", "1", False),
    ])
    out = format_merged(merge_results([r]), fmt="csv")
    assert "myapp,2,1" in out


# ── cli_merger helpers ─────────────────────────────────────────────────────

def test_cmd_merger_missing_file(tmp_path, capsys):
    from depwatch.cli_merger import _cmd_merger

    class A:
        history_files = [str(tmp_path / "nope.json")]
        fmt = "text"

    rc = _cmd_merger(A())
    assert rc == 1
    captured = capsys.readouterr()
    assert "No results" in captured.err or "not found" in captured.err


def test_cmd_merger_valid_file(tmp_path, capsys):
    from depwatch.cli_merger import _cmd_merger

    hist = tmp_path / "hist.json"
    entry = {
        "project": "demo",
        "timestamp": "2024-01-01T00:00:00",
        "packages": [{"name": "click", "current": "8.0", "latest": "8.1", "outdated": True}],
    }
    hist.write_text(json.dumps([entry]))

    class A:
        history_files = [str(hist)]
        fmt = "text"

    rc = _cmd_merger(A())
    assert rc == 0
    out = capsys.readouterr().out
    assert "demo" in out
