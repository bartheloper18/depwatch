"""Tests for depwatch.archiver."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from depwatch.archiver import archive_info, archive_old_entries, restore_archive
from depwatch.history import save_history


PROJECT = "myapp"


def _entry(ts: str, outdated: int = 0) -> dict:
    return {
        "timestamp": ts,
        "project": PROJECT,
        "project_type": "python",
        "packages": [
            {"name": f"pkg{i}", "current": "1.0.0", "latest": "2.0.0", "outdated": True}
            for i in range(outdated)
        ],
    }


@pytest.fixture()
def dirs(tmp_path: Path):
    hist = tmp_path / "history.json"
    arch = tmp_path / "archive"
    return hist, arch


def test_archive_nothing_when_under_keep(dirs):
    hist, arch = dirs
    entries = [_entry(f"2024-01-0{i+1}T00:00:00") for i in range(3)]
    save_history(hist, entries)

    archived = archive_old_entries(hist, arch, PROJECT, keep=10)

    assert archived == 0
    assert not arch.exists()


def test_archive_moves_oldest_entries(dirs):
    hist, arch = dirs
    entries = [_entry(f"2024-01-{i+1:02d}T00:00:00") for i in range(10)]
    save_history(hist, entries)

    archived = archive_old_entries(hist, arch, PROJECT, keep=6)

    assert archived == 4

    remaining = json.loads(hist.read_text())
    assert len(remaining) == 6
    # Most-recent entries are kept
    assert remaining[0]["timestamp"] == "2024-01-05T00:00:00"


def test_archive_appends_to_existing_zip(dirs):
    hist, arch = dirs

    # First pass – archive 2 entries
    entries_a = [_entry(f"2024-01-0{i+1}T00:00:00") for i in range(4)]
    save_history(hist, entries_a)
    archive_old_entries(hist, arch, PROJECT, keep=2)

    # Second pass – archive 2 more
    entries_b = [_entry(f"2024-02-0{i+1}T00:00:00") for i in range(4)]
    save_history(hist, entries_b)
    archive_old_entries(hist, arch, PROJECT, keep=2)

    zip_path = arch / f"{PROJECT}_archive.zip"
    with zipfile.ZipFile(zip_path, "r") as zf:
        stored = json.loads(zf.read("entries.json"))

    assert len(stored) == 4  # 2 from first pass + 2 from second pass


def test_restore_archive_prepends_entries(dirs):
    hist, arch = dirs
    entries = [_entry(f"2024-01-{i+1:02d}T00:00:00") for i in range(8)]
    save_history(hist, entries)
    archive_old_entries(hist, arch, PROJECT, keep=4)

    restored = restore_archive(arch, PROJECT, hist)

    assert restored == 4
    all_entries = json.loads(hist.read_text())
    assert len(all_entries) == 8
    zip_path = arch / f"{PROJECT}_archive.zip"
    assert not zip_path.exists()


def test_restore_archive_missing_returns_zero(dirs):
    hist, arch = dirs
    save_history(hist, [])
    result = restore_archive(arch, PROJECT, hist)
    assert result == 0


def test_archive_info_no_archive(dirs):
    _, arch = dirs
    info = archive_info(arch, PROJECT)
    assert info["exists"] is False
    assert info["entry_count"] == 0


def test_archive_info_with_archive(dirs):
    hist, arch = dirs
    entries = [_entry(f"2024-01-{i+1:02d}T00:00:00") for i in range(6)]
    save_history(hist, entries)
    archive_old_entries(hist, arch, PROJECT, keep=3)

    info = archive_info(arch, PROJECT)
    assert info["exists"] is True
    assert info["entry_count"] == 3
    assert info["size_bytes"] > 0
