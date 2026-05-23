"""Simple interval-based scheduler for depwatch daemon mode."""

import logging
import time
from typing import Callable

logger = logging.getLogger(__name__)


class Scheduler:
    """Run a callable repeatedly at a fixed interval.

    Args:
        interval_seconds: How often to invoke *task* (in seconds).
        task: A zero-argument callable executed on each tick.
    """

    def __init__(self, interval_seconds: int, task: Callable[[], None]) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be a positive integer.")
        self.interval_seconds = interval_seconds
        self.task = task
        self._running = False

    def start(self) -> None:
        """Start the scheduler loop (blocking)."""
        self._running = True
        logger.info(
            "Scheduler started — running every %d second(s).", self.interval_seconds
        )
        try:
            while self._running:
                logger.debug("Scheduler tick: invoking task.")
                try:
                    self.task()
                except Exception as exc:  # noqa: BLE001
                    logger.error("Task raised an exception: %s", exc)
                time.sleep(self.interval_seconds)
        except KeyboardInterrupt:
            logger.info("Scheduler interrupted by user.")
        finally:
            self._running = False
            logger.info("Scheduler stopped.")

    def stop(self) -> None:
        """Signal the scheduler to stop after the current sleep."""
        self._running = False

    @property
    def is_running(self) -> bool:
        """Return True while the scheduler loop is active."""
        return self._running
