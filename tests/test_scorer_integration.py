"""Integration tests: scorer works end-to-end with real CheckResult data."""
import json
import pytest
from depwatch.checker import CheckResult, PackageStatus
from depwatch.scorer import score_result, HealthScore
from depwatch.history import save_history, load_history
from depwatch.cli_scorer import _result_from_entry


def _ps(name, current, latest, outdated=True):
    return PackageStatus(name=name, current=current, latest=latest, is_outdated=outdated)


@pytest.fixture
def hist_file(tmp_path):
    return tmp_path / "history.json"


def _make_entry(project, pkgs):
    return {
        "project": project,
        "project_type": "python",
        "packages": [
            {"name": p.name, "current": p.current, "latest": p.latest, "is_outdated": p.is_outdated}
            for p in pkgs
        ],
    }


def test_full_pipeline_all_up_to_date():
    pkgs = [_ps("a", "1.0.0", "1.0.0", False), _ps("b", "2.0.0", "2.0.0", False)]
    result = CheckResult(project="clean", project_type="python", packages=pkgs)
    hs = score_result(result)
    assert hs.overall == pytest.approx(1.0)
    assert hs.grade == "A"
    assert all(ps.score == 1.0 for ps in hs.package_scores)


def test_full_pipeline_critical_state():
    pkgs = [
        _ps("django", "2.0.0", "4.0.0"),
        _ps("flask", "1.0.0", "3.0.0"),
        _ps("requests", "1.0.0", "2.0.0"),
    ]
    result = CheckResult(project="legacy", project_type="python", packages=pkgs)
    hs = score_result(result)
    assert hs.overall == pytest.approx(0.1)
    assert hs.grade == "F"


def test_roundtrip_via_history(hist_file):
    pkgs = [_ps("lodash", "4.0.0", "4.17.21")]
    entry = _make_entry("webapp", pkgs)
    hist_file.write_text(json.dumps([entry]))

    history = load_history(str(hist_file))
    assert len(history) == 1
    result = _result_from_entry(history[0])
    hs = score_result(result)

    assert hs.project == "webapp"
    assert 0.0 <= hs.overall <= 1.0
    assert hs.grade in ("A", "B", "C", "D", "F")


def test_grade_improves_after_patch_upgrade():
    before_pkgs = [_ps("lib", "1.0.0", "2.0.0")]  # major bump
    after_pkgs = [_ps("lib", "2.0.0", "2.0.0", False)]  # up-to-date

    before = score_result(CheckResult("p", "python", before_pkgs))
    after = score_result(CheckResult("p", "python", after_pkgs))

    assert after.overall > before.overall
