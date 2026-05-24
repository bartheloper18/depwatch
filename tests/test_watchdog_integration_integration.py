"""Integration tests: watchdog_integration wired to real filesystem events via emit_event."""
from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from depwatch.watchdog_integration import (
    WatchEvent,
    WatchSession,
    create_session,
    emit_event,
)


@pytest.fixture()
def tmp_roots(tmp_path):
    root_a = tmp_path / "proj_a"
    root_b = tmp_path / "proj_b"
    root_a.mkdir()
    root_b.mkdir()
    return [root_a, root_b]


def test_full_roundtrip_events_collected(tmp_roots):
    """Events emitted into an active session are all delivered to the callback."""
    received: list[WatchEvent] = []
    session = create_session(roots=tmp_roots, callback=received.append)

    dep_files = [
        tmp_roots[0] / "requirements.txt",
        tmp_roots[1] / "package.json",
        tmp_roots[0] / "pyproject.toml",
    ]
    for f in dep_files:
        emit_event(session, f, event_type="modified")

    assert len(received) == 3
    paths = {ev.path for ev in received}
    assert paths == set(dep_files)


def test_deactivated_session_drops_events(tmp_roots):
    received: list[WatchEvent] = []
    session = create_session(roots=tmp_roots, callback=received.append)

    emit_event(session, tmp_roots[0] / "requirements.txt")
    session.deactivate()
    emit_event(session, tmp_roots[0] / "requirements.txt")  # should be dropped

    assert len(received) == 1


def test_concurrent_emit_all_events_delivered(tmp_roots):
    """Events from multiple threads are all delivered without loss."""
    received: list[WatchEvent] = []
    lock = threading.Lock()

    def cb(ev: WatchEvent) -> None:
        with lock:
            received.append(ev)

    session = create_session(roots=tmp_roots, callback=cb)
    n = 50
    threads = [
        threading.Thread(
            target=emit_event,
            args=(session, tmp_roots[0] / f"req{i}.txt"),
        )
        for i in range(n)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(received) == n


def test_reactivate_session_resumes_delivery(tmp_roots):
    received: list[WatchEvent] = []
    session = create_session(roots=tmp_roots, callback=received.append)

    session.deactivate()
    emit_event(session, tmp_roots[0] / "requirements.txt")  # dropped

    session.activate()
    emit_event(session, tmp_roots[0] / "requirements.txt")  # delivered

    assert len(received) == 1
