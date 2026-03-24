from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path


LOGGER = logging.getLogger(__name__)
CONFIG_FILE_NAME = "volumeswitch_config.json"


@dataclass
class DeviceConfig:
    id: str = ""
    name: str = ""


@dataclass
class AppConfig:
    primary: DeviceConfig = field(default_factory=DeviceConfig)
    secondary: DeviceConfig = field(default_factory=DeviceConfig)
    hotkey: str = ""
    autostart: bool = False
    start_minimized: bool = True
    show_notifications: bool = True
    fallback_to_primary_on_unknown: bool = True

    @property
    def is_complete(self) -> bool:
        return bool(self.primary.id and self.secondary.id)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AppConfig":
        primary = DeviceConfig(**(data.get("primary") or {}))
        secondary = DeviceConfig(**(data.get("secondary") or {}))
        return cls(
            primary=primary,
            secondary=secondary,
            hotkey=str(data.get("hotkey", "") or ""),
            autostart=bool(data.get("autostart", False)),
            start_minimized=bool(data.get("start_minimized", True)),
            show_notifications=bool(data.get("show_notifications", True)),
            fallback_to_primary_on_unknown=bool(
                data.get("fallback_to_primary_on_unknown", True)
            ),
        )


class ConfigManager:
    def __init__(self, app_dir: Path) -> None:
        self.app_dir = app_dir
        self.path = app_dir / CONFIG_FILE_NAME

    def load(self) -> AppConfig:
        if not self.path.exists():
            return AppConfig()

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception as exc:
            LOGGER.exception("Failed to load config: %s", exc)
            self._backup_corrupt_config()
            return AppConfig()

        try:
            return AppConfig.from_dict(data)
        except Exception as exc:
            LOGGER.exception("Invalid config structure: %s", exc)
            self._backup_corrupt_config()
            return AppConfig()

    def save(self, config: AppConfig) -> None:
        self.app_dir.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(config.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _backup_corrupt_config(self) -> None:
        if not self.path.exists():
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_path = self.path.with_name(
                f"{self.path.stem}.broken-{timestamp}{self.path.suffix}"
            )
            self.path.replace(backup_path)
            LOGGER.warning("Backed up corrupt config to %s", backup_path)
        except Exception:
            LOGGER.exception("Failed to back up corrupt config")
