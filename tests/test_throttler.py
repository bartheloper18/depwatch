"""Unit tests for depwatch.throttler."""
from __future__ import annotations

import time

import pytest

from depwatch.throttler import Throttler, ThrottleState


# ---------------------------------------------------------------------------
# ThrottleState
# ---------------------------------------------------------------------------

def test_throttle_state_str():
    s = ThrottleState(tokens=2.5)
    assert "2.5" in str(s) or "ThrottleState" in str(s)


# ---------------------------------------------------------------------------
# Throttler.allow
# ---------------------------------------------------------------------------

def test_allow_first_call_succeeds():
    t = Throttler(rate=1.0, capacity=1.0)
    assert t.allow("k") is True


def test_allow_second_call_immediately_fails():
    t = Throttler(rate=1.0, capacity=1.0)
    t.allow("k")
    assert t.allow("k") is False


def test_allow_capacity_three_allows_three_calls():
    t = Throttler(rate=0.0, capacity=3.0)  # no refill
    assert t.allow("k") is True
    assert t.allow("k") is True
    assert t.allow("k") is True
    assert t.allow("k") is False


def test_allow_different_keys_are_independent():
    t = Throttler(rate=0.0, capacity=1.0)
    assert t.allow("a") is True
    assert t.allow("b") is True
    assert t.allow("a") is False
    assert t.allow("b") is False


def test_allow_default_key_used_when_no_key_given():
    t = Throttler(rate=0.0, capacity=1.0)
    assert t.allow() is True
    assert t.allow() is False


# ---------------------------------------------------------------------------
# Throttler.reset
# ---------------------------------------------------------------------------

def test_reset_refills_single_key():
    t = Throttler(rate=0.0, capacity=1.0)
    t.allow("k")
    assert t.allow("k") is False
    t.reset("k")
    assert t.allow("k") is True


def test_reset_all_refills_every_key():
    t = Throttler(rate=0.0, capacity=1.0)
    t.allow("a")
    t.allow("b")
    t.reset_all()
    assert t.allow("a") is True
    assert t.allow("b") is True


def test_reset_nonexistent_key_is_noop():
    t = Throttler(rate=0.0, capacity=1.0)
    t.reset("ghost")  # should not raise


# ---------------------------------------------------------------------------
# Throttler.tracked_keys
# ---------------------------------------------------------------------------

def test_tracked_keys_empty_initially():
    t = Throttler()
    assert t.tracked_keys == []


def test_tracked_keys_populated_after_allow():
    t = Throttler()
    t.allow("x")
    t.allow("y")
    assert set(t.tracked_keys) == {"x", "y"}


# ---------------------------------------------------------------------------
# Refill over time (fast, using monkeypatch)
# ---------------------------------------------------------------------------

def test_refill_over_time(monkeypatch):
    """After waiting the equivalent of 1 second, a new token should appear."""
    clock = [0.0]
    monkeypatch.setattr("depwatch.throttler.time.monotonic", lambda: clock[0])

    t = Throttler(rate=1.0, capacity=1.0)
    t.allow("k")          # consume the token
    assert t.allow("k") is False

    clock[0] = 1.1        # advance 1.1 s — enough for one token
    assert t.allow("k") is True
