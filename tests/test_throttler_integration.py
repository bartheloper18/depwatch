"""Integration tests: throttler wired into a simulated check loop."""
from __future__ import annotations

from depwatch.throttler import Throttler


def _run_checks(throttler: Throttler, project: str, attempts: int) -> int:
    """Simulate *attempts* check requests; return how many were executed."""
    executed = 0
    for _ in range(attempts):
        if throttler.allow(project):
            executed += 1
    return executed


def test_throttler_limits_rapid_checks():
    """With capacity=2 and no refill, only 2 of 5 attempts execute."""
    t = Throttler(rate=0.0, capacity=2.0)
    executed = _run_checks(t, "my-project", attempts=5)
    assert executed == 2


def test_throttler_independent_projects():
    """Two projects each get their own independent bucket."""
    t = Throttler(rate=0.0, capacity=1.0)
    assert _run_checks(t, "proj-a", 3) == 1
    assert _run_checks(t, "proj-b", 3) == 1


def test_throttler_reset_between_runs():
    """After a reset, the project can run again."""
    t = Throttler(rate=0.0, capacity=1.0)
    assert _run_checks(t, "proj", 2) == 1
    t.reset("proj")
    assert _run_checks(t, "proj", 2) == 1


def test_throttler_high_rate_allows_many(monkeypatch):
    """With a high rate and advancing clock, many checks are allowed."""
    clock = [0.0]
    monkeypatch.setattr("depwatch.throttler.time.monotonic", lambda: clock[0])

    t = Throttler(rate=10.0, capacity=10.0)
    # Consume all tokens
    for _ in range(10):
        t.allow("p")
    assert t.allow("p") is False

    # Advance 1 second → 10 new tokens
    clock[0] = 1.0
    executed = _run_checks(t, "p", attempts=10)
    assert executed == 10
