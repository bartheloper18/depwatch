"""Integration tests: baseline round-trip via save/load/compare."""
from __future__ import annotations

from depwatch.baseline import load_baseline, new_since_baseline, save_baseline
from depwatch.checker import CheckResult, PackageStatus


def _ps(name, installed, latest):
    return PackageStatus(name=name, installed=installed, latest=latest)


def _result(*packages):
    return CheckResult(project="integration", packages=list(packages))


def test_full_roundtrip_no_new_issues(tmp_path):
    bfile = str(tmp_path / "baseline.json")
    initial = _result(_ps("django", "4.2.0", "4.2.0"), _ps("requests", "2.28.0", "2.31.0"))
    save_baseline(initial, bfile)

    # Same state later — no new issues
    later = _result(_ps("django", "4.2.0", "4.2.0"), _ps("requests", "2.28.0", "2.31.0"))
    baseline = load_baseline(bfile)
    new = new_since_baseline(later, baseline)
    assert new == []


def test_new_package_appears_after_baseline(tmp_path):
    bfile = str(tmp_path / "baseline.json")
    initial = _result(_ps("django", "4.2.0", "4.2.0"))
    save_baseline(initial, bfile)

    later = _result(
        _ps("django", "4.2.0", "4.2.0"),
        _ps("celery", "5.2.0", "5.4.0"),  # newly outdated
    )
    baseline = load_baseline(bfile)
    new = new_since_baseline(later, baseline)
    assert len(new) == 1
    assert new[0].name == "celery"


def test_all_up_to_date_returns_empty(tmp_path):
    bfile = str(tmp_path / "baseline.json")
    initial = _result(_ps("flask", "3.0.0", "3.0.0"))
    save_baseline(initial, bfile)

    later = _result(_ps("flask", "3.0.0", "3.0.0"))
    baseline = load_baseline(bfile)
    new = new_since_baseline(later, baseline)
    assert new == []


def test_baseline_upgrade_clears_old_issues(tmp_path):
    bfile = str(tmp_path / "baseline.json")
    # First baseline recorded while requests was outdated
    v1 = _result(_ps("requests", "2.28.0", "2.31.0"))
    save_baseline(v1, bfile)

    # Developer upgrades and re-records baseline
    v2 = _result(_ps("requests", "2.31.0", "2.31.0"))
    save_baseline(v2, bfile)

    # Now requests is up-to-date, no new issues
    current = _result(_ps("requests", "2.31.0", "2.31.0"))
    baseline = load_baseline(bfile)
    new = new_since_baseline(current, baseline)
    assert new == []
