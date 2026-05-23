"""Tag check results with user-defined labels for filtering and organisation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from depwatch.checker import CheckResult


# tag store: maps project_name -> list[str]
TagStore = Dict[str, List[str]]


def load_tags(path: Path) -> TagStore:
    """Load tag store from *path*; return empty dict when file is absent or corrupt."""
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if isinstance(data, dict):
            return {k: list(v) for k, v in data.items() if isinstance(v, list)}
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return {}


def save_tags(path: Path, store: TagStore) -> None:
    """Persist *store* to *path*, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(store, indent=2), encoding="utf-8")


def add_tag(store: TagStore, project: str, tag: str) -> TagStore:
    """Return a new store with *tag* added to *project* (idempotent)."""
    tags = list(store.get(project, []))
    if tag not in tags:
        tags.append(tag)
    return {**store, project: tags}


def remove_tag(store: TagStore, project: str, tag: str) -> TagStore:
    """Return a new store with *tag* removed from *project* (no-op if absent)."""
    tags = [t for t in store.get(project, []) if t != tag]
    updated = dict(store)
    if tags:
        updated[project] = tags
    else:
        updated.pop(project, None)
    return updated


def tags_for(store: TagStore, project: str) -> List[str]:
    """Return the list of tags for *project* (empty list when unknown)."""
    return list(store.get(project, []))


def filter_results_by_tag(
    results: List[CheckResult], store: TagStore, tag: str
) -> List[CheckResult]:
    """Return only those results whose project carries *tag*."""
    return [r for r in results if tag in store.get(r.project, [])]
