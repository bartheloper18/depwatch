"""Unit tests for depwatch.cli_throttler."""
from __future__ import annotations

import argparse

import pytest

from depwatch.throttler import Throttler
from depwatch.cli_throttler import add_throttler_subcommand, _cmd_throttler


class _FakeArgs:
    def __init__(self, reset=None, check=None):
        self.reset = reset
        self.check = check


# ---------------------------------------------------------------------------
# add_throttler_subcommand
# ---------------------------------------------------------------------------

def test_add_throttler_subcommand_registers_parser():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_throttler_subcommand(subs)
    args = parser.parse_args(["throttler"])
    assert hasattr(args, "func")


# ---------------------------------------------------------------------------
# _cmd_throttler — reset
# ---------------------------------------------------------------------------

def test_cmd_throttler_reset_single_key(capsys):
    t = Throttler(rate=0.0, capacity=1.0)
    t.allow("proj")  # exhaust
    args = _FakeArgs(reset="proj")
    rc = _cmd_throttler(args, throttler=t)
    assert rc == 0
    out = capsys.readouterr().out
    assert "proj" in out
    # After reset the key should be allowed again
    assert t.allow("proj") is True


def test_cmd_throttler_reset_all(capsys):
    t = Throttler(rate=0.0, capacity=1.0)
    t.allow("a")
    t.allow("b")
    args = _FakeArgs(reset="all")
    rc = _cmd_throttler(args, throttler=t)
    assert rc == 0
    assert t.allow("a") is True
    assert t.allow("b") is True


# ---------------------------------------------------------------------------
# _cmd_throttler — check
# ---------------------------------------------------------------------------

def test_cmd_throttler_check_allowed(capsys):
    t = Throttler(rate=0.0, capacity=1.0)
    args = _FakeArgs(check="myproject")
    rc = _cmd_throttler(args, throttler=t)
    assert rc == 0
    out = capsys.readouterr().out
    assert "allowed" in out


def test_cmd_throttler_check_throttled(capsys):
    t = Throttler(rate=0.0, capacity=1.0)
    t.allow("myproject")  # exhaust
    args = _FakeArgs(check="myproject")
    rc = _cmd_throttler(args, throttler=t)
    assert rc == 0
    out = capsys.readouterr().out
    assert "throttled" in out


# ---------------------------------------------------------------------------
# _cmd_throttler — list
# ---------------------------------------------------------------------------

def test_cmd_throttler_list_empty(capsys):
    t = Throttler()
    args = _FakeArgs()
    rc = _cmd_throttler(args, throttler=t)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No throttle" in out


def test_cmd_throttler_list_with_keys(capsys):
    t = Throttler()
    t.allow("alpha")
    args = _FakeArgs()
    rc = _cmd_throttler(args, throttler=t)
    assert rc == 0
    out = capsys.readouterr().out
    assert "alpha" in out
