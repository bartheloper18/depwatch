"""Prune old history entries to keep the history file manageable."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import List

from depwatch.history import load_history, save_history

logger = logging.getLogger(__name__)

DEFAULT_MAX_ENTRIES = 100
DEFAULT_MAX_AGE_DAYS = 30


def prune_by_count(entries: List[dict], max_entries: int = DEFAULT_MAX_ENTRIES) -> List[dict]:
    """Return only the *max_entries* most recent entries."""
    if len(entries) <= max_entries:
        return entries
    return entries[-max_entries:]


def prune_by_age(entries: List[dict], max_age_days: int = DEFAULT_MAX_AGE_DAYS) -> List[dict]:
    """Return only entries newer than *max_age_days* days."""
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=max_age_days)
    kept = []
    for entry in entries:
        ts = entry.get("timestamp")
        if ts is None:
            kept.append(entry)
            continue
        try:
            entry_time = datetime.fromisoformat(ts)
            if entry_time.tzinfo is None:
                entry_time = entry_time.replace(tzinfo=timezone.utc)
            if entry_time >= cutoff:
                kept.append(entry)
        except ValueError:
            kept.append(entry)
    return kept


def prune_history(
    history_path: str,
    max_entries: int = DEFAULT_MAX_ENTRIES,
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
) -> int:
    """Load, prune, and save history. Returns number of entries removed."""
    entries = load_history(history_path)
    original_count = len(entries)

    entries = prune_by_age(entries, max_age_days)
    entries = prune_by_count(entries, max_entries)

    removed = original_count - len(entries)
    if removed > 0:
        save_history(history_path, entries)
        logger.info("Pruned %d old history entries from %s", removed, history_path)
    else:
        logger.debug("No history entries pruned from %s", history_path)

    return removed
