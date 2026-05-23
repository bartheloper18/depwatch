"""Persist and retrieve check results history for trend tracking."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import List, Optional

DEFAULT_HISTORY_PATH = os.path.expanduser("~/.depwatch/history.json")
MAX_HISTORY_ENTRIES = 100


def _entry_from_result(result) -> dict:
    """Serialize a CheckResult into a history entry dict."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "project": result.project_name,
        "project_type": result.project_type,
        "total": len(result.packages),
        "outdated": len(result.outdated_packages),
        "packages": [
            {
                "name": p.name,
                "current": p.current_version,
                "latest": p.latest_version,
                "outdated": p.is_outdated,
            }
            for p in result.packages
        ],
    }


def load_history(path: str = DEFAULT_HISTORY_PATH) -> List[dict]:
    """Load persisted history entries from *path*.

    Returns an empty list if the file does not exist or is malformed.
    """
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def save_history(entries: List[dict], path: str = DEFAULT_HISTORY_PATH) -> None:
    """Persist *entries* to *path*, trimming to MAX_HISTORY_ENTRIES."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    trimmed = entries[-MAX_HISTORY_ENTRIES:]
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(trimmed, fh, indent=2)


def record_result(result, path: str = DEFAULT_HISTORY_PATH) -> List[dict]:
    """Append a CheckResult to the history file and return updated entries."""
    entries = load_history(path)
    entries.append(_entry_from_result(result))
    save_history(entries, path)
    return entries


def latest_entry(project: str, path: str = DEFAULT_HISTORY_PATH) -> Optional[dict]:
    """Return the most recent history entry for *project*, or None."""
    entries = load_history(path)
    for entry in reversed(entries):
        if entry.get("project") == project:
            return entry
    return None
