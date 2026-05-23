"""Tests for depwatch.baseline"""
from __future__ import annotations

import json
import os

import pytest

from depwatch.baseline import (
    Baseline,
    load_baseline,
    new_since_baseline,
    save_baseline,
)
from depwatch.checker import CheckResult, PackageStatus


def _ps(name: str, installed: str, latest: str) -> PackageStatus:
    return PackageStatus(name=name, installed=installed, latest=latest)


def _make_result(packages: list[PackageStatus]) -> CheckResult:
    return CheckResult(project="myapp", packages=packages)


@pytest.fixture()
def baseline_path(tmp_path):
    return str(tmp_path / ".depwatch" / "baseline.json")


def test_save_creates_file(baseline_path):
    result = _make_result([_ps("requests", "2.28.0", "2.31.0")])
    save_baseline(result, baseline_path)
    assert os.path.exists(baseline_path)


def test_save_and_load_roundtrip(baseline_path):
    result = _make_result([
        _ps("flask", "2.0.0", "2.0.0"),
        _ps("requests", "2.28.0", "2.31.0"),
    ])
    saved = save_baseline(result, baseline_path)
    loaded = load_baseline(baseline_path)

    assert loaded is not None
    assert loaded.project == "myapp"
    assert loaded.packages == saved.packages
    assert "flask" in loaded.packages
    assert loaded.packages["flask"] == "2.0.0"


def test_load_missing_returns_none(tmp_path):
    result = load_baseline(str(tmp_path / "nonexistent.json"))
    assert result is None


def test_load_malformed_returns_none(tmp_path):
    bad = tmp_path / "baseline.json"
    bad.write_text("not json")
    assert load_baseline(str(bad)) is None


def test_load_incomplete_json_returns_none(tmp_path):
    bad = tmp_path / "baseline.json"
    bad.write_text(json.dumps({"project": "x"}))
    assert load_baseline(str(bad)) is None


def test_new_since_baseline_none_returns_all_outdated():
    packages = [
        _ps("requests", "2.28.0", "2.31.0"),
        _ps("flask", "2.0.0", "2.0.0"),
    ]
    result = _make_result(packages)
    new = new_since_baseline(result, None)
    assert len(new) == 1
    assert new[0].name == "requests"


def test_new_since_baseline_no_change():
    packages = [_ps("requests", "2.28.0", "2.31.0")]
    result = _make_result(packages)
    baseline = Baseline(project="myapp", recorded_at="2024-01-01T00:00:00+00:00",
                        packages={"requests": "2.28.0"})
    new = new_since_baseline(result, baseline)
    assert new == []


def test_new_since_baseline_version_changed():
    packages = [_ps("requests", "2.29.0", "2.31.0")]
    result = _make_result(packages)
    # Baseline recorded an older installed version
    baseline = Baseline(project="myapp", recorded_at="2024-01-01T00:00:00+00:00",
                        packages={"requests": "2.28.0"})
    new = new_since_baseline(result, baseline)
    assert len(new) == 1


def test_new_since_baseline_brand_new_package():
    packages = [
        _ps("requests", "2.28.0", "2.31.0"),
        _ps("boto3", "1.26.0", "1.34.0"),
    ]
    result = _make_result(packages)
    baseline = Baseline(project="myapp", recorded_at="2024-01-01T00:00:00+00:00",
                        packages={"requests": "2.28.0"})
    new = new_since_baseline(result, baseline)
    assert len(new) == 1
    assert new[0].name == "boto3"
