"""Integration tests: grouper works end-to-end with history + checker types."""

from __future__ import annotations

import json
import pathlib

import pytest

from depwatch.checker import CheckResult, PackageStatus
from depwatch.grouper import group_result, group_results
from depwatch.history import record_result, latest_entry


def _ps(name: str, current: str, latest: str, outdated: bool = True) -> PackageStatus:
    return PackageStatus(name=name, current_version=current, latest_version=latest, outdated=outdated)


@pytest.fixture()
def hist_file(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path / "history.json"


def test_roundtrip_group_from_history(hist_file):
    """Record a result to history, reload it, group it — counts must match."""
    result = CheckResult(
        project_name="webapp",
        packages=[
            _ps("django", "3.0.0", "4.2.0"),    # critical
            _ps("pillow", "9.0.0", "9.5.0"),    # moderate
            _ps("six", "1.16.0", "1.16.0", outdated=False),
        ],
    )
    record_result(str(hist_file), result)

    entry = latest_entry(str(hist_file))
    assert entry is not None

    pkgs = [
        PackageStatus(
            name=p["name"],
            current_version=p["current_version"],
            latest_version=p["latest_version"],
            outdated=p["outdated"],
        )
        for p in entry["packages"]
    ]
    reloaded = CheckResult(project_name=entry["project_name"], packages=pkgs)
    grouped = group_result(reloaded)

    assert grouped.project_name == "webapp"
    assert len(grouped.critical) == 1
    assert grouped.critical[0].name == "django"
    assert len(grouped.moderate) == 1
    assert len(grouped.up_to_date) == 1


def test_group_results_all_up_to_date():
    results = [
        CheckResult(
            project_name=f"proj{i}",
            packages=[_ps(f"pkg{i}", "1.0.0", "1.0.0", outdated=False)],
        )
        for i in range(3)
    ]
    mapping = group_results(results)
    for name, grouped in mapping.items():
        assert grouped.total_outdated == 0
        assert len(grouped.up_to_date) == 1
