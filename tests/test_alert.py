"""Tests for depwatch.alert module."""
import json
import os
from datetime import datetime, timedelta

import pytest

from depwatch.alert import (
    AlertState,
    DEFAULT_ALERT_COOLDOWN_HOURS,
    load_alert_state,
    save_alert_state,
    should_alert,
)


@pytest.fixture
def alert_path(tmp_path):
    return str(tmp_path / "alert_state.json")


# --- AlertState unit tests ---

def test_was_recently_alerted_no_entry():
    state = AlertState()
    assert state.was_recently_alerted("myproject") is False


def test_mark_and_check_recently_alerted():
    state = AlertState()
    state.mark_alerted("myproject")
    assert state.was_recently_alerted("myproject") is True


def test_was_recently_alerted_expired():
    state = AlertState()
    old_ts = (datetime.utcnow() - timedelta(hours=48)).isoformat()
    state.last_alerted["myproject"] = old_ts
    assert state.was_recently_alerted("myproject", cooldown_hours=24) is False


def test_was_recently_alerted_within_window():
    state = AlertState()
    recent_ts = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    state.last_alerted["myproject"] = recent_ts
    assert state.was_recently_alerted("myproject", cooldown_hours=24) is True


# --- Persistence tests ---

def test_load_alert_state_missing_file(alert_path):
    state = load_alert_state(alert_path)
    assert state.last_alerted == {}


def test_load_alert_state_malformed_file(alert_path):
    with open(alert_path, "w") as fh:
        fh.write("not valid json{{{")
    state = load_alert_state(alert_path)
    assert state.last_alerted == {}


def test_save_and_load_roundtrip(alert_path):
    state = AlertState()
    state.mark_alerted("proj_a")
    state.mark_alerted("proj_b")
    save_alert_state(state, alert_path)

    loaded = load_alert_state(alert_path)
    assert set(loaded.last_alerted.keys()) == {"proj_a", "proj_b"}


# --- should_alert logic ---

def test_should_alert_no_outdated():
    state = AlertState()
    assert should_alert("proj", has_outdated=False, state=state) is False


def test_should_alert_first_time():
    state = AlertState()
    assert should_alert("proj", has_outdated=True, state=state) is True


def test_should_alert_suppressed_within_cooldown():
    state = AlertState()
    state.mark_alerted("proj")
    assert should_alert("proj", has_outdated=True, state=state, cooldown_hours=24) is False


def test_should_alert_after_cooldown_expired():
    state = AlertState()
    old_ts = (datetime.utcnow() - timedelta(hours=30)).isoformat()
    state.last_alerted["proj"] = old_ts
    assert should_alert("proj", has_outdated=True, state=state, cooldown_hours=24) is True
