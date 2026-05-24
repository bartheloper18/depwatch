"""Integration between depwatch FileWatcher and the watchdog library.

Provides a higher-level interface for watching dependency files and
triggering callbacks when changes are detected.
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class WatchEvent:
    """Represents a file-change event on a watched dependency file."""
    path: Path
    event_type: str  # 'modified' | 'created' | 'deleted'

    def __str__(self) -> str:
        return f"WatchEvent({self.event_type}: {self.path})"


@dataclass
class WatchSession:
    """Tracks an active watch session with its registered paths and callbacks."""
    roots: List[Path]
    callback: Callable[[WatchEvent], None]
    _active: bool = field(default=False, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def activate(self) -> None:
        with self._lock:
            self._active = True
        logger.debug("WatchSession activated for roots: %s", self.roots)

    def deactivate(self) -> None:
        with self._lock:
            self._active = False
        logger.debug("WatchSession deactivated")

    @property
    def is_active(self) -> bool:
        with self._lock:
            return self._active

    def dispatch(self, event: WatchEvent) -> None:
        """Dispatch a watch event to the registered callback if session is active."""
        if not self.is_active:
            logger.debug("Session inactive; dropping event %s", event)
            return
        try:
            self.callback(event)
        except Exception:
            logger.exception("Error in watch callback for event %s", event)


def create_session(
    roots: List[Path],
    callback: Callable[[WatchEvent], None],
) -> WatchSession:
    """Create and activate a new WatchSession."""
    session = WatchSession(roots=[Path(r) for r in roots], callback=callback)
    session.activate()
    return session


def emit_event(
    session: WatchSession,
    path: Path,
    event_type: str = "modified",
) -> None:
    """Emit a WatchEvent into a session (useful for testing and manual triggers)."""
    event = WatchEvent(path=Path(path), event_type=event_type)
    session.dispatch(event)
