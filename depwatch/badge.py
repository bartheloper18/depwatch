"""Generate status badge data for depwatch projects."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from depwatch.checker import CheckResult

BadgeColor = Literal["brightgreen", "yellow", "red", "lightgrey"]


@dataclass
class BadgeData:
    label: str
    message: str
    color: BadgeColor
    schema_version: int = 1

    def to_dict(self) -> dict:
        return {
            "schemaVersion": self.schema_version,
            "label": self.label,
            "message": self.message,
            "color": self.color,
        }

    def __str__(self) -> str:
        return f"[{self.label}: {self.message}]"


def _choose_color(outdated: int, total: int) -> BadgeColor:
    if total == 0:
        return "lightgrey"
    if outdated == 0:
        return "brightgreen"
    ratio = outdated / total
    if ratio < 0.25:
        return "yellow"
    return "red"


def build_badge(result: CheckResult) -> BadgeData:
    """Build badge data from a CheckResult."""
    total = len(result.packages)
    outdated = len(result.outdated_packages())
    color = _choose_color(outdated, total)
    if total == 0:
        message = "no packages"
    elif outdated == 0:
        message = "up to date"
    else:
        message = f"{outdated}/{total} outdated"
    return BadgeData(
        label=result.project_name,
        message=message,
        color=color,
    )


def save_badge(badge: BadgeData, path: Path) -> None:
    """Write badge JSON (Shields.io endpoint format) to *path*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(badge.to_dict(), indent=2))


def load_badge(path: Path) -> BadgeData:
    """Load a previously saved badge from *path*."""
    data = json.loads(path.read_text())
    return BadgeData(
        schema_version=data.get("schemaVersion", 1),
        label=data["label"],
        message=data["message"],
        color=data["color"],
    )
