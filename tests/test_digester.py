"""Tests for depwatch.digester."""
import pytest
from depwatch.checker import CheckResult, PackageStatus
from depwatch.digester import (
    DigestEntry,
    Digest,
    build_digest,
    format_digest,
    _result_to_entry,
)


def _ps(name: str, current: str, latest: str) -> PackageStatus:
    return PackageStatus(
        name=name,
        current_version=current,
        latest_version=latest,
        is_outdated=current != latest,
    )


def _make_result(project: str, project_type: str, pkgs) -> CheckResult:
    return CheckResult(
        project=project,
        project_type=project_type,
        packages=pkgs,
        checked_at="2024-01-01T00:00:00+00:00",
    )


def test_result_to_entry_all_up_to_date():
    result = _make_result("myapp", "python", [_ps("requests", "2.28.0", "2.28.0")])
    entry = _result_to_entry(result)
    assert entry.project == "myapp"
    assert entry.outdated_count == 0
    assert entry.total_packages == 1


def test_result_to_entry_some_outdated():
    pkgs = [
        _ps("requests", "2.27.0", "2.28.0"),
        _ps("flask", "2.0.0", "2.0.0"),
    ]
    result = _make_result("myapp", "python", pkgs)
    entry = _result_to_entry(result)
    assert entry.outdated_count == 1
    assert entry.total_packages == 2


def test_digest_entry_str_up_to_date():
    entry = DigestEntry("proj", "node", 5, 0, "2024-01-01T00:00:00+00:00")
    assert "up-to-date" in str(entry)
    assert "proj" in str(entry)


def test_digest_entry_str_outdated():
    entry = DigestEntry("proj", "node", 5, 3, "2024-01-01T00:00:00+00:00")
    assert "3 outdated" in str(entry)


def test_build_digest_empty():
    digest = build_digest([])
    assert digest.entries == []
    assert digest.total_outdated == 0
    assert not digest.has_issues


def test_build_digest_multiple_results():
    r1 = _make_result("a", "python", [_ps("x", "1.0", "2.0")])
    r2 = _make_result("b", "node", [_ps("y", "3.0", "3.0")])
    digest = build_digest([r1, r2])
    assert len(digest.entries) == 2
    assert digest.total_outdated == 1
    assert digest.has_issues


def test_format_digest_text_contains_project():
    r = _make_result("myproj", "python", [_ps("dep", "0.1", "0.2")])
    digest = build_digest([r])
    output = format_digest(digest, fmt="text")
    assert "myproj" in output
    assert "Total outdated" in output


def test_format_digest_markdown_has_table():
    r = _make_result("webapp", "node", [_ps("lodash", "4.0.0", "4.17.21")])
    digest = build_digest([r])
    output = format_digest(digest, fmt="markdown")
    assert "|" in output
    assert "webapp" in output
    assert "Total outdated packages" in output


def test_digest_str_includes_generated_at():
    digest = build_digest([])
    assert "generated at" in str(digest).lower()
