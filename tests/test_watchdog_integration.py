"""Tests for depwatch.watchdog_integration."""
from __future__ import annotations

import threading
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from depwatch.watchdog_integration import (
    WatchEvent,
    WatchSession,
    create_session,
    emit_event,
)


# ---------------------------------------------------------------------------
# WatchEvent
# ---------------------------------------------------------------------------

def test_watch_event_str_contains_type_and_path():
    ev = WatchEvent(path=Path("/proj/requirements.txt"), event_type="modified")
    text = str(ev)
    assert "modified" in text
    assert "requirements.txt" in text


# ---------------------------------------------------------------------------
# WatchSession lifecycle
# ---------------------------------------------------------------------------

def test_session_starts_inactive():
    session = WatchSession(roots=[Path("/proj")], callback=MagicMock())
    assert not session.is_active


def test_activate_makes_session_active():
    session = WatchSession(roots=[Path("/proj")], callback=MagicMock())
    session.activate()
    assert session.is_active


def test_deactivate_makes_session_inactive():
    session = WatchSession(roots=[Path("/proj")], callback=MagicMock())
    session.activate()
    session.deactivate()
    assert not session.is_active


# ---------------------------------------------------------------------------
# WatchSession.dispatch
# ---------------------------------------------------------------------------

def test_dispatch_calls_callback_when_active():
    cb = MagicMock()
    session = WatchSession(roots=[Path("/proj")], callback=cb)
    session.activate()
    ev = WatchEvent(path=Path("/proj/package.json"), event_type="created")
    session.dispatch(ev)
    cb.assert_called_once_with(ev)


def test_dispatch_does_not_call_callback_when_inactive():
    cb = MagicMock()
    session = WatchSession(roots=[Path("/proj")], callback=cb)
    ev = WatchEvent(path=Path("/proj/package.json"), event_type="modified")
    session.dispatch(ev)  # session not activated
    cb.assert_not_called()


def test_dispatch_swallows_callback_exception():
    def bad_cb(ev):
        raise RuntimeError("boom")

    session = WatchSession(roots=[Path("/proj")], callback=bad_cb)
    session.activate()
    ev = WatchEvent(path=Path("/proj/requirements.txt"), event_type="modified")
    # Should not raise
    session.dispatch(ev)


# ---------------------------------------------------------------------------
# create_session helper
# ---------------------------------------------------------------------------

def test_create_session_returns_active_session():
    cb = MagicMock()
    session = create_session(roots=[Path("/proj")], callback=cb)
    assert session.is_active


def test_create_session_coerces_roots_to_path():
    cb = MagicMock()
    session = create_session(roots=["/proj/a", "/proj/b"], callback=cb)  # type: ignore[list-item]
    assert all(isinstance(r, Path) for r in session.roots)


# ---------------------------------------------------------------------------
# emit_event helper
# ---------------------------------------------------------------------------

def test_emit_event_triggers_callback():
    received = []
    session = create_session(roots=[Path("/proj")], callback=received.append)
    emit_event(session, Path("/proj/requirements.txt"), event_type="modified")
    assert len(received) == 1
    assert received[0].event_type == "modified"
    assert received[0].path == Path("/proj/requirements.txt")


def test_emit_event_default_type_is_modified():
    received = []
    session = create_session(roots=[Path("/proj")], callback=received.append)
    emit_event(session, Path("/proj/package.json"))
    assert received[0].event_type == "modified"


def test_emit_event_thread_safety():
    """Multiple threads emitting events should not corrupt the callback list."""
    received = []
    lock = threading.Lock()

    def cb(ev):
        with lock:
            received.append(ev)

    session = create_session(roots=[Path("/proj")], callback=cb)
    threads = [
        threading.Thread(target=emit_event, args=(session, Path(f"/proj/req{i}.txt")))
        for i in range(20)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(received) == 20
