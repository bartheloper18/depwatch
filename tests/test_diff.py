"""Tests for depwatch.diff."""

import json
import pytest

from depwatch.checker import PackageStatus
from depwatch.diff import (
    CheckDiff,
    PackageDiff,
    diff_results,
    diff_latest,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ps(name: str, current: str, latest: str) -> PackageStatus:
    return PackageStatus(name=name, current=current, latest=latest)


@pytest.fixture()
def hist_path(tmp_path):
    return tmp_path / "history.json"


def _write_entries(path, entries):
    path.write_text(json.dumps(entries))


# ---------------------------------------------------------------------------
# diff_results
# ---------------------------------------------------------------------------

def test_diff_results_no_change():
    prev = [_ps("requests", "2.28.0", "2.28.0")]
    curr = [_ps("requests", "2.28.0", "2.28.0")]
    diffs = diff_results(prev, curr)
    assert len(diffs) == 1
    d = diffs[0]
    assert not d.became_outdated
    assert not d.became_current
    assert not d.is_new
    assert not d.was_removed


def test_diff_results_became_outdated():
    prev = [_ps("flask", "2.3.0", "2.3.0")]
    curr = [_ps("flask", "2.3.0", "3.0.0")]
    diffs = diff_results(prev, curr)
    assert diffs[0].became_outdated is True
    assert diffs[0].became_current is False


def test_diff_results_became_current():
    prev = [_ps("flask", "2.3.0", "3.0.0")]
    curr = [_ps("flask", "3.0.0", "3.0.0")]
    diffs = diff_results(prev, curr)
    assert diffs[0].became_current is True
    assert diffs[0].became_outdated is False


def test_diff_results_new_package():
    prev = []
    curr = [_ps("numpy", "1.26.0", "1.26.0")]
    diffs = diff_results(prev, curr)
    assert diffs[0].is_new is True
    assert diffs[0].was_removed is False


def test_diff_results_removed_package():
    prev = [_ps("numpy", "1.26.0", "1.26.0")]
    curr = []
    diffs = diff_results(prev, curr)
    assert diffs[0].was_removed is True
    assert diffs[0].is_new is False


# ---------------------------------------------------------------------------
# PackageDiff.__str__
# ---------------------------------------------------------------------------

def test_package_diff_str_outdated():
    d = PackageDiff("flask", "2.3.0", "2.3.0", "2.3.0", "3.0.0",
                    became_outdated=True, became_current=False, is_new=False, was_removed=False)
    assert "OUTDATED" in str(d)


def test_package_diff_str_new():
    d = PackageDiff("numpy", None, "1.26.0", None, "1.26.0",
                    became_outdated=False, became_current=False, is_new=True, was_removed=False)
    assert "NEW" in str(d)


# ---------------------------------------------------------------------------
# CheckDiff.has_changes
# ---------------------------------------------------------------------------

def test_check_diff_has_changes_false_when_all_unchanged():
    prev = [_ps("requests", "2.28.0", "2.28.0")]
    curr = [_ps("requests", "2.28.0", "2.28.0")]
    cd = CheckDiff(project="myapp", changes=diff_results(prev, curr))
    assert cd.has_changes is False


def test_check_diff_has_changes_true_when_outdated():
    prev = [_ps("flask", "2.3.0", "2.3.0")]
    curr = [_ps("flask", "2.3.0", "3.0.0")]
    cd = CheckDiff(project="myapp", changes=diff_results(prev, curr))
    assert cd.has_changes is True


# ---------------------------------------------------------------------------
# diff_latest
# ---------------------------------------------------------------------------

def test_diff_latest_returns_none_when_insufficient_history(hist_path):
    _write_entries(hist_path, [
        {"project": "myapp", "packages": [{"name": "flask", "current": "2.3.0", "latest": "2.3.0"}]}
    ])
    result = diff_latest("myapp", str(hist_path))
    assert result is None


def test_diff_latest_returns_diff_for_two_entries(hist_path):
    _write_entries(hist_path, [
        {"project": "myapp", "packages": [{"name": "flask", "current": "2.3.0", "latest": "2.3.0"}]},
        {"project": "myapp", "packages": [{"name": "flask", "current": "2.3.0", "latest": "3.0.0"}]},
    ])
    result = diff_latest("myapp", str(hist_path))
    assert result is not None
    assert result.project == "myapp"
    assert result.changes[0].became_outdated is True


def test_diff_latest_ignores_other_projects(hist_path):
    _write_entries(hist_path, [
        {"project": "other", "packages": []},
        {"project": "myapp", "packages": [{"name": "flask", "current": "2.3.0", "latest": "2.3.0"}]},
    ])
    result = diff_latest("myapp", str(hist_path))
    assert result is None  # only one entry for 'myapp'
