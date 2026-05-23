"""Summary module: aggregates history entries into a human-readable digest."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from depwatch.history import load_history


@dataclass
class ProjectSummary:
    project_path: str
    total_checks: int
    last_checked: Optional[datetime]
    last_outdated_count: int
    ever_had_outdated: bool

    def __str__(self) -> str:
        ts = self.last_checked.strftime("%Y-%m-%d %H:%M UTC") if self.last_checked else "never"
        status = f"{self.last_outdated_count} outdated" if self.last_outdated_count else "up-to-date"
        return (
            f"[{self.project_path}] checks={self.total_checks}, "
            f"last={ts}, status={status}"
        )


def summarise(history_path: str) -> List[ProjectSummary]:
    """Return one ProjectSummary per unique project found in the history file."""
    entries = load_history(history_path)
    projects: dict[str, list] = {}
    for entry in entries:
        projects.setdefault(entry["project_path"], []).append(entry)

    summaries: List[ProjectSummary] = []
    for path, records in projects.items():
        records_sorted = sorted(records, key=lambda r: r.get("checked_at", ""))
        latest = records_sorted[-1]

        last_checked: Optional[datetime] = None
        raw_ts = latest.get("checked_at")
        if raw_ts:
            try:
                last_checked = datetime.fromisoformat(raw_ts).replace(tzinfo=timezone.utc)
            except ValueError:
                pass

        outdated = latest.get("outdated_packages", [])
        ever_outdated = any(r.get("outdated_packages") for r in records)

        summaries.append(
            ProjectSummary(
                project_path=path,
                total_checks=len(records),
                last_checked=last_checked,
                last_outdated_count=len(outdated),
                ever_had_outdated=ever_outdated,
            )
        )
    return summaries


def format_summary(history_path: str) -> str:
    """Return a plain-text summary digest for all projects in the history file."""
    items = summarise(history_path)
    if not items:
        return "No history recorded yet."
    lines = ["=== depwatch summary ==="]
    for item in items:
        lines.append(str(item))
    return "\n".join(lines)
