"""File system watcher that triggers re-checks when dependency files change."""

import logging
import threading
from pathlib import Path
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)

_WATCHED_FILENAMES = {
    "requirements.txt",
    "pyproject.toml",
    "setup.cfg",
    "package.json",
    "package-lock.json",
    "yarn.lock",
}


class FileWatcher:
    """Polls dependency files for modifications and invokes a callback on change."""

    def __init__(
        self,
        paths: List[Path],
        callback: Callable[[Path], None],
        poll_interval: float = 5.0,
    ) -> None:
        self._paths = paths
        self._callback = callback
        self._poll_interval = poll_interval
        self._mtimes: dict[Path, float] = {}
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the background polling thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("FileWatcher is already running.")
            return
        self._stop_event.clear()
        self._mtimes = self._snapshot()
        self._thread = threading.Thread(target=self._run, daemon=True, name="depwatch-watcher")
        self._thread.start()
        logger.info("FileWatcher started (interval=%.1fs, files=%d)", self._poll_interval, len(self._paths))

    def stop(self) -> None:
        """Signal the polling thread to stop and wait for it."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self._poll_interval + 2)
        logger.info("FileWatcher stopped.")

    @property
    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run(self) -> None:
        while not self._stop_event.wait(self._poll_interval):
            self._check_for_changes()

    def _check_for_changes(self) -> None:
        current = self._snapshot()
        for path, mtime in current.items():
            previous = self._mtimes.get(path)
            if previous is None:
                logger.debug("New file detected: %s", path)
                self._callback(path)
            elif mtime != previous:
                logger.debug("File changed: %s", path)
                self._callback(path)
        self._mtimes = current

    def _snapshot(self) -> dict:
        result: dict[Path, float] = {}
        for p in self._paths:
            try:
                result[p] = p.stat().st_mtime
            except FileNotFoundError:
                pass
        return result


def collect_watched_files(project_roots: List[Path]) -> List[Path]:
    """Return all recognised dependency files found under *project_roots*."""
    found: List[Path] = []
    for root in project_roots:
        for name in _WATCHED_FILENAMES:
            candidate = root / name
            if candidate.exists():
                found.append(candidate)
    return found
