"""Tests for depwatch.exporter."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from depwatch.checker import CheckResult, PackageStatus
from depwatch.exporter import export_csv, export_json, export_results


def _make_result(project: str = "myapp", project_type: str = "python") -> CheckResult:
    packages = [
        PackageStatus(name="requests", current_version="2.28.0", latest_version="2.31.0"),
        PackageStatus(name="flask", current_version="2.3.0", latest_version="2.3.0"),
    ]
    return CheckResult(project_name=project, project_type=project_type, packages=packages)


# ---------------------------------------------------------------------------
# export_json
# ---------------------------------------------------------------------------

def test_export_json_creates_file(tmp_path: Path) -> None:
    out = tmp_path / "results.json"
    export_json([_make_result()], out)
    assert out.exists()


def test_export_json_valid_structure(tmp_path: Path) -> None:
    out = tmp_path / "results.json"
    export_json([_make_result()], out)
    data = json.loads(out.read_text())
    assert isinstance(data, list)
    assert len(data) == 2  # two packages
    assert data[0]["project"] == "myapp"
    assert data[0]["package"] == "requests"
    assert data[0]["outdated"] is True
    assert data[1]["outdated"] is False


def test_export_json_multiple_results(tmp_path: Path) -> None:
    out = tmp_path / "results.json"
    export_json([_make_result("app1"), _make_result("app2")], out)
    data = json.loads(out.read_text())
    assert len(data) == 4
    projects = {row["project"] for row in data}
    assert projects == {"app1", "app2"}


# ---------------------------------------------------------------------------
# export_csv
# ---------------------------------------------------------------------------

def test_export_csv_creates_file(tmp_path: Path) -> None:
    out = tmp_path / "results.csv"
    export_csv([_make_result()], out)
    assert out.exists()


def test_export_csv_has_header(tmp_path: Path) -> None:
    out = tmp_path / "results.csv"
    export_csv([_make_result()], out)
    reader = csv.DictReader(out.read_text().splitlines())
    assert set(reader.fieldnames or []) >= {"project", "package", "outdated"}


def test_export_csv_row_count(tmp_path: Path) -> None:
    out = tmp_path / "results.csv"
    export_csv([_make_result()], out)
    rows = list(csv.DictReader(out.read_text().splitlines()))
    assert len(rows) == 2


# ---------------------------------------------------------------------------
# export_results dispatch
# ---------------------------------------------------------------------------

def test_export_results_json(tmp_path: Path) -> None:
    out = tmp_path / "out.json"
    export_results([_make_result()], out, fmt="json")
    json.loads(out.read_text())  # should not raise


def test_export_results_csv(tmp_path: Path) -> None:
    out = tmp_path / "out.csv"
    export_results([_make_result()], out, fmt="csv")
    rows = list(csv.DictReader(out.read_text().splitlines()))
    assert len(rows) == 2


def test_export_results_unknown_format_raises(tmp_path: Path) -> None:
    out = tmp_path / "out.xml"
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_results([_make_result()], out, fmt="xml")
