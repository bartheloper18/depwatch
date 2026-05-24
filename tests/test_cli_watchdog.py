"""Tests for depwatch.cli_watchdog."""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from depwatch.cli_watchdog import _cmd_watchdog, add_watchdog_subcommand


class _FakeArgs:
    def __init__(self, roots, verbose=False):
        self.roots = roots
        self.verbose = verbose


# ---------------------------------------------------------------------------
# add_watchdog_subcommand
# ---------------------------------------------------------------------------

def test_add_watchdog_subcommand_registers_parser():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="command")
    add_watchdog_subcommand(subs)
    args = parser.parse_args(["watchdog", "--roots", "/tmp"])
    assert args.command == "watchdog"
    assert args.roots == ["/tmp"]


def test_add_watchdog_subcommand_verbose_default_false():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="command")
    add_watchdog_subcommand(subs)
    args = parser.parse_args(["watchdog", "--roots", "/tmp"])
    assert args.verbose is False


# ---------------------------------------------------------------------------
# _cmd_watchdog – missing root returns error
# ---------------------------------------------------------------------------

def test_cmd_watchdog_missing_root_returns_1(tmp_path):
    missing = tmp_path / "nonexistent"
    args = _FakeArgs(roots=[str(missing)])
    result = _cmd_watchdog(args)
    assert result == 1


# ---------------------------------------------------------------------------
# _cmd_watchdog – valid root starts watcher
# ---------------------------------------------------------------------------

def test_cmd_watchdog_starts_watcher(tmp_path):
    args = _FakeArgs(roots=[str(tmp_path)])

    mock_watcher = MagicMock()
    mock_session = MagicMock()
    mock_session.is_active = True

    import signal as _signal

    def fake_pause():
        # Simulate SIGINT by calling the registered handler immediately
        handler = _signal.getsignal(_signal.SIGINT)
        if callable(handler):
            handler(None, None)

    with patch("depwatch.cli_watchdog.FileWatcher", return_value=mock_watcher), \
         patch("depwatch.cli_watchdog.create_session", return_value=mock_session), \
         patch("depwatch.cli_watchdog.emit_event"), \
         patch("signal.pause", side_effect=fake_pause), \
         pytest.raises(SystemExit) as exc_info:
        _cmd_watchdog(args)

    assert exc_info.value.code == 0
    mock_watcher.start.assert_called_once()
    mock_watcher.stop.assert_called_once()
    mock_session.deactivate.assert_called_once()


def test_cmd_watchdog_multiple_roots(tmp_path):
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    root_a.mkdir()
    root_b.mkdir()
    args = _FakeArgs(roots=[str(root_a), str(root_b)])

    mock_watcher = MagicMock()
    mock_session = MagicMock()

    with patch("depwatch.cli_watchdog.FileWatcher", return_value=mock_watcher), \
         patch("depwatch.cli_watchdog.create_session", return_value=mock_session) as mock_cs, \
         patch("signal.pause", side_effect=SystemExit(0)), \
         pytest.raises(SystemExit):
        _cmd_watchdog(args)

    call_roots = mock_cs.call_args[1]["roots"]
    assert len(call_roots) == 2
