"""Tests for depwatch.tagger."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from depwatch.checker import CheckResult, PackageStatus
from depwatch.scanner import ProjectType
from depwatch.tagger import (
    add_tag,
    filter_results_by_tag,
    load_tags,
    remove_tag,
    save_tags,
    tags_for,
)


@pytest.fixture()
def tag_path(tmp_path: Path) -> Path:
    return tmp_path / "tags.json"


def _ps(name: str, current: str = "1.0.0", latest: str = "1.0.0") -> PackageStatus:
    return PackageStatus(name=name, current_version=current, latest_version=latest)


def _make_result(project: str, *statuses: PackageStatus) -> CheckResult:
    return CheckResult(project=project, project_type=ProjectType.PYTHON, packages=list(statuses))


# --- load / save ---

def test_load_tags_missing_file(tag_path: Path) -> None:
    assert load_tags(tag_path) == {}


def test_load_tags_malformed_file(tag_path: Path) -> None:
    tag_path.write_text("not json", encoding="utf-8")
    assert load_tags(tag_path) == {}


def test_save_and_load_roundtrip(tag_path: Path) -> None:
    store = {"myproject": ["production", "critical"]}
    save_tags(tag_path, store)
    loaded = load_tags(tag_path)
    assert loaded == store


def test_save_creates_parent_dirs(tmp_path: Path) -> None:
    nested = tmp_path / "a" / "b" / "tags.json"
    save_tags(nested, {"p": ["t"]})
    assert nested.exists()


# --- add / remove ---

def test_add_tag_new_project() -> None:
    store = add_tag({}, "proj", "ci")
    assert store == {"proj": ["ci"]}


def test_add_tag_idempotent() -> None:
    store = add_tag({"proj": ["ci"]}, "proj", "ci")
    assert store["proj"].count("ci") == 1


def test_add_tag_appends_to_existing() -> None:
    store = add_tag({"proj": ["ci"]}, "proj", "prod")
    assert "prod" in store["proj"]
    assert "ci" in store["proj"]


def test_remove_tag_existing() -> None:
    store = remove_tag({"proj": ["ci", "prod"]}, "proj", "ci")
    assert store == {"proj": ["prod"]}


def test_remove_tag_last_tag_removes_project_key() -> None:
    store = remove_tag({"proj": ["ci"]}, "proj", "ci")
    assert "proj" not in store


def test_remove_tag_absent_tag_is_noop() -> None:
    original = {"proj": ["ci"]}
    store = remove_tag(original, "proj", "missing")
    assert store == original


# --- tags_for ---

def test_tags_for_unknown_project() -> None:
    assert tags_for({}, "unknown") == []


def test_tags_for_known_project() -> None:
    assert tags_for({"p": ["a", "b"]}, "p") == ["a", "b"]


# --- filter_results_by_tag ---

def test_filter_results_by_tag_matches() -> None:
    r1 = _make_result("alpha", _ps("requests"))
    r2 = _make_result("beta", _ps("flask"))
    store = {"alpha": ["production"]}
    filtered = filter_results_by_tag([r1, r2], store, "production")
    assert filtered == [r1]


def test_filter_results_by_tag_no_match() -> None:
    r1 = _make_result("alpha", _ps("requests"))
    filtered = filter_results_by_tag([r1], {}, "production")
    assert filtered == []


def test_filter_results_by_tag_empty_list() -> None:
    assert filter_results_by_tag([], {"p": ["t"]}, "t") == []
