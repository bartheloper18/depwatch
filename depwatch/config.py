"""Configuration model for depwatch."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import List, Optional

DEFAULT_CHECK_INTERVAL = 3600  # seconds
DEFAULT_ALERT_COOLDOWN_HOURS = 24


@dataclass
class DepwatchConfig:
    project_roots: List[str] = field(default_factory=list)
    check_interval: int = DEFAULT_CHECK_INTERVAL
    alert_cooldown_hours: int = DEFAULT_ALERT_COOLDOWN_HOURS
    alert_state_path: str = ".depwatch/alert_state.json"
    history_path: str = ".depwatch/history.json"
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None
    email_recipients: List[str] = field(default_factory=list)
    report_format: str = "text"


def from_dict(data: dict) -> DepwatchConfig:
    cfg = DepwatchConfig()
    cfg.project_roots = data.get("project_roots", [])
    cfg.check_interval = data.get("check_interval", DEFAULT_CHECK_INTERVAL)
    cfg.alert_cooldown_hours = data.get("alert_cooldown_hours", DEFAULT_ALERT_COOLDOWN_HOURS)
    cfg.alert_state_path = data.get("alert_state_path", ".depwatch/alert_state.json")
    cfg.history_path = data.get("history_path", ".depwatch/history.json")
    cfg.smtp_host = data.get("smtp_host")
    cfg.smtp_port = data.get("smtp_port", 587)
    cfg.smtp_user = data.get("smtp_user")
    cfg.smtp_password = data.get("smtp_password")
    cfg.email_from = data.get("email_from")
    cfg.email_recipients = data.get("email_recipients", [])
    cfg.report_format = data.get("report_format", "text")
    return cfg


def to_dict(cfg: DepwatchConfig) -> dict:
    return {
        "project_roots": cfg.project_roots,
        "check_interval": cfg.check_interval,
        "alert_cooldown_hours": cfg.alert_cooldown_hours,
        "alert_state_path": cfg.alert_state_path,
        "history_path": cfg.history_path,
        "smtp_host": cfg.smtp_host,
        "smtp_port": cfg.smtp_port,
        "smtp_user": cfg.smtp_user,
        "smtp_password": cfg.smtp_password,
        "email_from": cfg.email_from,
        "email_recipients": cfg.email_recipients,
        "report_format": cfg.report_format,
    }


def load_config(path: str) -> DepwatchConfig:
    if not os.path.exists(path):
        return DepwatchConfig()
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return from_dict(data)


def save_config(cfg: DepwatchConfig, path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(to_dict(cfg), fh, indent=2)
