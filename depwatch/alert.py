"""Alert threshold and suppression logic for depwatch."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional

DEFAULT_ALERT_COOLDOWN_HOURS = 24


@dataclass
class AlertState:
    """Tracks when a project was last alerted."""
    last_alerted: Dict[str, str] = field(default_factory=dict)  # project -> ISO timestamp

    def was_recently_alerted(self, project: str, cooldown_hours: int = DEFAULT_ALERT_COOLDOWN_HOURS) -> bool:
        """Return True if the project was alerted within the cooldown window."""
        ts = self.last_alerted.get(project)
        if ts is None:
            return False
        last = datetime.fromisoformat(ts)
        return datetime.utcnow() - last < timedelta(hours=cooldown_hours)

    def mark_alerted(self, project: str) -> None:
        """Record that an alert was sent for this project right now."""
        self.last_alerted[project] = datetime.utcnow().isoformat()


def load_alert_state(path: str) -> AlertState:
    """Load alert state from a JSON file; return empty state if missing or corrupt."""
    if not os.path.exists(path):
        return AlertState()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return AlertState(last_alerted=data.get("last_alerted", {}))
    except (json.JSONDecodeError, KeyError, TypeError):
        return AlertState()


def save_alert_state(state: AlertState, path: str) -> None:
    """Persist alert state to a JSON file."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"last_alerted": state.last_alerted}, fh, indent=2)


def should_alert(
    project: str,
    has_outdated: bool,
    state: AlertState,
    cooldown_hours: int = DEFAULT_ALERT_COOLDOWN_HOURS,
) -> bool:
    """Decide whether an alert should be fired for *project*.

    Returns True only when there are outdated packages AND the project has not
    been alerted within the cooldown window.
    """
    if not has_outdated:
        return False
    return not state.was_recently_alerted(project, cooldown_hours)
