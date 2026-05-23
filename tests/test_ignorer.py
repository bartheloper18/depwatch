"""Tests for depwatch.ignorer."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from depwatch.checker import CheckResult, PackageStatus
from depwatch.ignorer import (
    add_to_ignore_list,
    filter_result,
    load_ignore_list,
    remove_from_ignore_list,
    save_ignore_list,
)


@pytest.fixture()
def ignore_path(tmp_path: Path) -> Path:
    return tmp_path / ".depwatch_ignore.json"


def _make_result(*names_and_flags: tuple[str, bool]) -> CheckResult:
    packages = [
        PackageStatus(
            name=name,
            current="1.0.0",
            latest="2.0.0" if outdated else "1.0.0",
            outdated=outdated,
        )
        for name, outdated in names_and_flags
    ]
    return CheckResult(
        project_name="proj",
        project_type="python",
        packages=packages,
        checked_at=datetime.now(tz=timezone.utc),
    )


def test_load_ignore_list_missing_file(ignore_path: Path) -> None:
    assert load_ignore_list(ignore_path) == []


def test_load_ignore_list_malformed_file(ignore_path: Path) -> None:
    ignore_path.write_text("not valid json", encoding="utf-8")
    assert load_ignore_list(ignore_path) == []


def test_save_and_load_roundtrip(ignore_path: Path) -> None:
    save_ignore_list(["requests", "flask", "click"], ignore_path)
    loaded = load_ignore_list(ignore_path)
    assert loaded == ["click", "flask", "requests"]


def test_save_deduplicates(ignore_path: Path) -> None:
    save_ignore_list(["requests", "requests", "flask"], ignore_path)
    loaded = load_ignore_list(ignore_path)
    assert loaded.count("requests") == 1


def test_add_to_ignore_list_new_package(ignore_path: Path) -> None:
    result = add_to_ignore_list("requests", ignore_path)
    assert "requests" in result
    assert load_ignore_list(ignore_path) == ["requests"]


def test_add_to_ignore_list_idempotent(ignore_path: Path) -> None:
    add_to_ignore_list("requests", ignore_path)
    result = add_to_ignore_list("requests", ignore_path)
    assert result.count("requests") == 1


def test_remove_from_ignore_list(ignore_path: Path) -> None:
    save_ignore_list(["requests", "flask"], ignore_path)
    result = remove_from_ignore_list("requests", ignore_path)
    assert "requests" not in result
    assert "flask" in result


def test_remove_nonexistent_is_ok(ignore_path: Path) -> None:
    save_ignore_list(["flask"], ignore_path)
    result = remove_from_ignore_list("requests", ignore_path)
    assert result == ["flask"]


def test_filter_result_removes_ignored_packages() -> None:
    result = _make_result(("requests", True), ("flask", False), ("click", True))
    filtered = filter_result(result, ["requests"])
    names = [p.name for p in filtered.packages]
    assert "requests" not in names
    assert "flask" in names
    assert "click" in names


def test_filter_result_empty_ignore_list_unchanged() -> None:
    result = _make_result(("requests", True), ("flask", False))
    filtered = filter_result(result, [])
    assert len(filtered.packages) == 2


def test_filter_result_preserves_metadata() -> None:
    result = _make_result(("requests", True))
    filtered = filter_result(result, ["other"])
    assert filtered.project_name == result.project_name
    assert filtered.project_type == result.project_type
    assert filtered.checked_at == result.checked_at
