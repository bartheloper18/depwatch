"""Tests for depwatch.streamer."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from depwatch.checker import CheckResult, PackageStatus
from depwatch.streamer import StreamEntry, _result_to_entry, stream_results, read_stream


def _ps(name: str, current: str, latest: str) -> PackageStatus:
    return PackageStatus(name=name, current_version=current, latest_version=latest)


def _make_result(project: str = "myapp", packages: list[PackageStatus] | None = None) -> CheckResult:
    if packages is None:
        packages = [_ps("requests", "2.28.0", "2.31.0"), _ps("flask", "3.0.0", "3.0.0")]
    return CheckResult(project=project, packages=packages)


def test_result_to_entry_counts_outdated():
    result = _make_result()
    entry = _result_to_entry(result)
    assert entry.project == "myapp"
    assert entry.total == 2
    assert entry.outdated == 1


def test_result_to_entry_packages_structure():
    result = _make_result()
    entry = _result_to_entry(result)
    assert len(entry.packages) == 2
    pkg = entry.packages[0]
    assert "name" in pkg
    assert "current" in pkg
    assert "latest" in pkg
    assert "outdated" in pkg


def test_stream_entry_to_dict_round_trips():
    entry = StreamEntry(
        project="proj",
        timestamp="2024-01-01T00:00:00+00:00",
        total=3,
        outdated=1,
        packages=[{"name": "x", "current": "1.0", "latest": "2.0", "outdated": True}],
    )
    d = entry.to_dict()
    assert d["project"] == "proj"
    assert d["total"] == 3
    assert d["outdated"] == 1


def test_stream_entry_str_is_valid_json():
    entry = StreamEntry(
        project="p", timestamp="ts", total=1, outdated=0, packages=[]
    )
    parsed = json.loads(str(entry))
    assert parsed["project"] == "p"


def test_stream_results_writes_to_file(tmp_path: Path):
    out = tmp_path / "stream.ndjson"
    results = [_make_result("a"), _make_result("b")]
    entries = stream_results(results, dest=out)
    assert len(entries) == 2
    lines = out.read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["project"] == "a"


def test_stream_results_append_mode(tmp_path: Path):
    out = tmp_path / "stream.ndjson"
    stream_results([_make_result("first")], dest=out)
    stream_results([_make_result("second")], dest=out, append=True)
    lines = out.read_text().splitlines()
    assert len(lines) == 2


def test_stream_results_overwrite_mode(tmp_path: Path):
    out = tmp_path / "stream.ndjson"
    stream_results([_make_result("first")], dest=out)
    stream_results([_make_result("second")], dest=out, append=False)
    lines = out.read_text().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["project"] == "second"


def test_read_stream_missing_file(tmp_path: Path):
    result = read_stream(tmp_path / "nonexistent.ndjson")
    assert result == []


def test_read_stream_roundtrip(tmp_path: Path):
    out = tmp_path / "stream.ndjson"
    stream_results([_make_result("proj")], dest=out)
    entries = read_stream(out)
    assert len(entries) == 1
    assert entries[0].project == "proj"
    assert entries[0].total == 2


def test_read_stream_skips_malformed_lines(tmp_path: Path):
    out = tmp_path / "stream.ndjson"
    out.write_text('{"project": "ok", "timestamp": "", "total": 0, "outdated": 0, "packages": []}\nnot-json\n')
    entries = read_stream(out)
    assert len(entries) == 1
    assert entries[0].project == "ok"
