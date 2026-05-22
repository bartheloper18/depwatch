"""Tests for depwatch configuration loader."""

import json
import os
import tempfile
import pytest

from depwatch.config import (
    DepwatchConfig,
    load_config,
    save_config,
    DEFAULT_CHECK_INTERVAL,
    DEFAULT_LOG_LEVEL,
)


@pytest.fixture
def tmp_config_path(tmp_path):
    return str(tmp_path / "config.json")


def test_default_config():
    config = DepwatchConfig()
    assert config.watch_paths == []
    assert config.check_interval == DEFAULT_CHECK_INTERVAL
    assert config.log_level == DEFAULT_LOG_LEVEL
    assert config.notify_email is None
    assert config.ignore_packages == []
    assert config.enable_vulnerability_check is True


def test_from_dict_partial():
    data = {"watch_paths": ["/projects/myapp"], "log_level": "DEBUG"}
    config = DepwatchConfig.from_dict(data)
    assert config.watch_paths == ["/projects/myapp"]
    assert config.log_level == "DEBUG"
    assert config.check_interval == DEFAULT_CHECK_INTERVAL


def test_to_dict_roundtrip():
    original = DepwatchConfig(
        watch_paths=["/srv/app"],
        check_interval=1800,
        log_level="WARNING",
        notify_email="dev@example.com",
        ignore_packages=["boto3"],
        enable_vulnerability_check=False,
    )
    restored = DepwatchConfig.from_dict(original.to_dict())
    assert restored == original


def test_load_config_missing_file(tmp_config_path):
    config = load_config(tmp_config_path)
    assert isinstance(config, DepwatchConfig)
    assert config.watch_paths == []


def test_save_and_load_config(tmp_config_path):
    config = DepwatchConfig(
        watch_paths=["/home/user/project"],
        check_interval=600,
        notify_email="alert@example.com",
    )
    save_config(config, tmp_config_path)
    assert os.path.exists(tmp_config_path)

    loaded = load_config(tmp_config_path)
    assert loaded.watch_paths == ["/home/user/project"]
    assert loaded.check_interval == 600
    assert loaded.notify_email == "alert@example.com"


def test_save_config_creates_directory(tmp_path):
    nested_path = str(tmp_path / "nested" / "dir" / "config.json")
    config = DepwatchConfig()
    save_config(config, nested_path)
    assert os.path.exists(nested_path)
