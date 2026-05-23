"""Tests for depwatch.config module."""
import json
import os

import pytest

from depwatch.config import (
    DEFAULT_ALERT_COOLDOWN_HOURS,
    DEFAULT_CHECK_INTERVAL,
    DepwatchConfig,
    from_dict,
    load_config,
    save_config,
    to_dict,
)


@pytest.fixture
def tmp_config_path(tmp_path):
    return str(tmp_path / "depwatch.json")


def test_default_config():
    cfg = DepwatchConfig()
    assert cfg.project_roots == []
    assert cfg.check_interval == DEFAULT_CHECK_INTERVAL
    assert cfg.alert_cooldown_hours == DEFAULT_ALERT_COOLDOWN_HOURS
    assert cfg.email_recipients == []
    assert cfg.report_format == "text"


def test_from_dict_partial():
    cfg = from_dict({"check_interval": 600, "project_roots": ["/tmp/proj"]})
    assert cfg.check_interval == 600
    assert cfg.project_roots == ["/tmp/proj"]
    assert cfg.smtp_host is None


def test_from_dict_alert_cooldown():
    cfg = from_dict({"alert_cooldown_hours": 12})
    assert cfg.alert_cooldown_hours == 12


def test_from_dict_alert_state_path():
    cfg = from_dict({"alert_state_path": "/custom/alert.json"})
    assert cfg.alert_state_path == "/custom/alert.json"


def test_to_dict_roundtrip():
    cfg = DepwatchConfig(
        project_roots=["/a", "/b"],
        check_interval=1800,
        alert_cooldown_hours=6,
        email_recipients=["ops@example.com"],
    )
    d = to_dict(cfg)
    restored = from_dict(d)
    assert restored.project_roots == ["/a", "/b"]
    assert restored.check_interval == 1800
    assert restored.alert_cooldown_hours == 6
    assert restored.email_recipients == ["ops@example.com"]


def test_load_config_missing_file(tmp_config_path):
    cfg = load_config(tmp_config_path)
    assert isinstance(cfg, DepwatchConfig)
    assert cfg.project_roots == []


def test_save_and_load_config(tmp_config_path):
    cfg = DepwatchConfig(
        project_roots=["/srv/app"],
        smtp_host="smtp.example.com",
        alert_cooldown_hours=48,
    )
    save_config(cfg, tmp_config_path)
    assert os.path.exists(tmp_config_path)

    loaded = load_config(tmp_config_path)
    assert loaded.project_roots == ["/srv/app"]
    assert loaded.smtp_host == "smtp.example.com"
    assert loaded.alert_cooldown_hours == 48


def test_save_config_creates_parent_dirs(tmp_path):
    nested_path = str(tmp_path / "nested" / "dir" / "config.json")
    cfg = DepwatchConfig()
    save_config(cfg, nested_path)
    assert os.path.exists(nested_path)
