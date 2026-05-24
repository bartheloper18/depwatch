"""archiver.py – compress and archive old history entries to a zip file."""
from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from depwatch.history import load_history, save_history


def _archive_filename(base_dir: Path, project: str) -> Path:
    """Return a deterministic archive path for *project* inside *base_dir*."""
    safe = project.replace("/", "_").replace("\\", "_")
    return base_dir / f"{safe}_archive.zip"


def archive_old_entries(
    history_path: Path,
    archive_dir: Path,
    project: str,
    keep: int = 50,
) -> int:
    """Move entries beyond the *keep* most-recent ones into a zip archive.

    Returns the number of entries archived.
    """
    entries = load_history(history_path)
    if len(entries) <= keep:
        return 0

    to_archive = entries[:-keep]
    to_keep = entries[-keep:]

    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = _archive_filename(archive_dir, project)

    existing: List[dict] = []
    if archive_path.exists():
        with zipfile.ZipFile(archive_path, "r") as zf:
            if "entries.json" in zf.namelist():
                existing = json.loads(zf.read("entries.json"))

    combined = existing + to_archive
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("entries.json", json.dumps(combined, indent=2))

    save_history(history_path, to_keep)
    return len(to_archive)


def restore_archive(archive_dir: Path, project: str, history_path: Path) -> int:
    """Prepend archived entries back into *history_path*.

    Returns the number of entries restored.
    """
    archive_path = _archive_filename(archive_dir, project)
    if not archive_path.exists():
        return 0

    with zipfile.ZipFile(archive_path, "r") as zf:
        if "entries.json" not in zf.namelist():
            return 0
        archived: List[dict] = json.loads(zf.read("entries.json"))

    current = load_history(history_path)
    save_history(history_path, archived + current)
    archive_path.unlink()
    return len(archived)


def archive_info(archive_dir: Path, project: str) -> dict:
    """Return metadata about an existing archive without restoring it."""
    archive_path = _archive_filename(archive_dir, project)
    if not archive_path.exists():
        return {"exists": False, "entry_count": 0, "size_bytes": 0}

    with zipfile.ZipFile(archive_path, "r") as zf:
        count = len(json.loads(zf.read("entries.json"))) if "entries.json" in zf.namelist() else 0

    return {
        "exists": True,
        "entry_count": count,
        "size_bytes": archive_path.stat().st_size,
        "path": str(archive_path),
    }
