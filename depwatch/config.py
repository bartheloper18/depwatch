"""Configuration loader for depwatch daemon."""

import os
import json
from dataclasses import dataclass, field
from typing import List, Optional


DEFAULT_CONFIG_PATH = os.path.expanduser("~/.depwatch/config.json")
DEFAULT_CHECK_INTERVAL = 3600  # seconds
DEFAULT_LOG_LEVEL = "INFO"


@dataclass
class DepwatchConfig:
    """Holds runtime configuration for the depwatch daemon."""

    watch_paths: List[str] = field(default_factory=list)
    check_interval: int = DEFAULT_CHECK_INTERVAL
    log_level: str = DEFAULT_LOG_LEVEL
    notify_email: Optional[str] = None
    ignore_packages: List[str] = field(default_factory=list)
    enable_vulnerability_check: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> "DepwatchConfig":
        return cls(
            watch_paths=data.get("watch_paths", []),
            check_interval=data.get("check_interval", DEFAULT_CHECK_INTERVAL),
            log_level=data.get("log_level", DEFAULT_LOG_LEVEL),
            notify_email=data.get("notify_email"),
            ignore_packages=data.get("ignore_packages", []),
            enable_vulnerability_check=data.get("enable_vulnerability_check", True),
        )

    def to_dict(self) -> dict:
        return {
            "watch_paths": self.watch_paths,
            "check_interval": self.check_interval,
            "log_level": self.log_level,
            "notify_email": self.notify_email,
            "ignore_packages": self.ignore_packages,
            "enable_vulnerability_check": self.enable_vulnerability_check,
        }


def load_config(path: str = DEFAULT_CONFIG_PATH) -> DepwatchConfig:
    """Load configuration from a JSON file, returning defaults if not found."""
    if not os.path.exists(path):
        return DepwatchConfig()
    with open(path, "r") as f:
        data = json.load(f)
    return DepwatchConfig.from_dict(data)


def save_config(config: DepwatchConfig, path: str = DEFAULT_CONFIG_PATH) -> None:
    """Persist configuration to a JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(config.to_dict(), f, indent=2)
