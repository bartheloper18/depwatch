"""Tests for depwatch.watcher."""

import time
from pathlib import Path

import pytest

from depwatch.watcher import FileWatcher, collect_watched_files


@pytest.fixture()
def tmp_dep_file(tmp_path: Path) -> Path:
    f = tmp_path / "requirements.txt"
    f.write_text("requests==2.28.0\n")
    return f


# ---------------------------------------------------------------------------
# collect_watched_files
# ---------------------------------------------------------------------------

def test_collect_watched_files_finds_known_files(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("")
    (tmp_path / "package.json").write_text("{}")
    (tmp_path / "ignored.txt").write_text("")

    found = collect_watched_files([tmp_path])
    names = {p.name for p in found}
    assert "requirements.txt" in names
    assert "package.json" in names
    assert "ignored.txt" not in names


def test_collect_watched_files_empty_dir(tmp_path: Path) -> None:
    assert collect_watched_files([tmp_path]) == []


def test_collect_watched_files_multiple_roots(tmp_path: Path) -> None:
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    root_a.mkdir()
    root_b.mkdir()
    (root_a / "pyproject.toml").write_text("")
    (root_b / "package-lock.json").write_text("")

    found = collect_watched_files([root_a, root_b])
    assert len(found) == 2


# ---------------------------------------------------------------------------
# FileWatcher lifecycle
# ---------------------------------------------------------------------------

def test_file_watcher_starts_and_stops(tmp_dep_file: Path) -> None:
    watcher = FileWatcher([tmp_dep_file], callback=lambda p: None, poll_interval=0.1)
    watcher.start()
    assert watcher.is_running
    watcher.stop()
    assert not watcher.is_running


def test_file_watcher_double_start_is_safe(tmp_dep_file: Path) -> None:
    watcher = FileWatcher([tmp_dep_file], callback=lambda p: None, poll_interval=0.1)
    watcher.start()
    watcher.start()  # should not raise
    watcher.stop()


def test_file_watcher_detects_modification(tmp_dep_file: Path) -> None:
    changed: list = []

    watcher = FileWatcher([tmp_dep_file], callback=lambda p: changed.append(p), poll_interval=0.05)
    watcher.start()
    time.sleep(0.1)

    tmp_dep_file.write_text("flask==2.3.0\n")
    time.sleep(0.3)

    watcher.stop()
    assert any(p == tmp_dep_file for p in changed)


def test_file_watcher_no_spurious_callbacks(tmp_dep_file: Path) -> None:
    changed: list = []

    watcher = FileWatcher([tmp_dep_file], callback=lambda p: changed.append(p), poll_interval=0.05)
    watcher.start()
    time.sleep(0.4)  # file not touched
    watcher.stop()

    assert changed == []
