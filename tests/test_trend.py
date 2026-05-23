"""Tests for depwatch.trend and depwatch.cli_trend."""
from __future__ import annotations

import json
import pytest

from depwatch.trend import TrendPoint, TrendSummary, build_trend, format_trend


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_history(path, entries):
    path.write_text(json.dumps(entries), encoding="utf-8")


def _entry(project, ts, pkgs):
    return {"project": project, "timestamp": ts, "packages": pkgs}


def _pkg(name, status):
    return {"name": name, "status": status}


# ---------------------------------------------------------------------------
# TrendPoint
# ---------------------------------------------------------------------------

def test_trend_point_str():
    pt = TrendPoint(timestamp="2024-01-01T00:00:00", outdated_count=3)
    assert "2024-01-01T00:00:00" in str(pt)
    assert "3 outdated" in str(pt)


# ---------------------------------------------------------------------------
# TrendSummary properties
# ---------------------------------------------------------------------------

def test_trend_summary_delta_improving():
    pts = [TrendPoint("t1", 5), TrendPoint("t2", 2)]
    ts = TrendSummary(project="myapp", points=pts)
    assert ts.delta == -3
    assert ts.direction == "improving"


def test_trend_summary_delta_worsening():
    pts = [TrendPoint("t1", 1), TrendPoint("t2", 4)]
    ts = TrendSummary(project="myapp", points=pts)
    assert ts.delta == 3
    assert ts.direction == "worsening"


def test_trend_summary_stable():
    pts = [TrendPoint("t1", 2), TrendPoint("t2", 2)]
    ts = TrendSummary(project="myapp", points=pts)
    assert ts.delta == 0
    assert ts.direction == "stable"


def test_trend_summary_single_point_no_delta():
    ts = TrendSummary(project="myapp", points=[TrendPoint("t1", 2)])
    assert ts.delta is None
    assert ts.direction == "stable"
    assert ts.latest is not None


def test_trend_summary_empty_points():
    ts = TrendSummary(project="myapp", points=[])
    assert ts.latest is None
    assert ts.delta is None


# ---------------------------------------------------------------------------
# build_trend
# ---------------------------------------------------------------------------

def test_build_trend_filters_by_project(tmp_path):
    hist = tmp_path / "h.json"
    _write_history(hist, [
        _entry("proj-a", "2024-01-01T00:00:00", [_pkg("requests", "outdated")]),
        _entry("proj-b", "2024-01-02T00:00:00", [_pkg("flask", "outdated"), _pkg("click", "outdated")]),
        _entry("proj-a", "2024-01-03T00:00:00", []),
    ])
    summary = build_trend(str(hist), "proj-a")
    assert summary.project == "proj-a"
    assert len(summary.points) == 2
    assert summary.points[0].outdated_count == 1
    assert summary.points[1].outdated_count == 0


def test_build_trend_missing_history_file(tmp_path):
    hist = tmp_path / "missing.json"
    summary = build_trend(str(hist), "proj-a")
    assert summary.points == []


def test_build_trend_unknown_project(tmp_path):
    hist = tmp_path / "h.json"
    _write_history(hist, [
        _entry("proj-a", "2024-01-01T00:00:00", []),
    ])
    summary = build_trend(str(hist), "proj-z")
    assert summary.points == []


# ---------------------------------------------------------------------------
# format_trend
# ---------------------------------------------------------------------------

def test_format_trend_no_data():
    ts = TrendSummary(project="myapp", points=[])
    text = format_trend(ts)
    assert "No data" in text


def test_format_trend_shows_direction():
    pts = [TrendPoint("2024-01-01T00:00:00", 3), TrendPoint("2024-01-02T00:00:00", 1)]
    ts = TrendSummary(project="myapp", points=pts)
    text = format_trend(ts)
    assert "improving" in text
    assert "-2" in text
