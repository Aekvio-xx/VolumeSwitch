from __future__ import annotations

import logging
import sys
import winreg
from pathlib import Path


LOGGER = logging.getLogger(__name__)
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE_NAME = "VolumeSwitch"


class StartupManager:
    def is_enabled(self) -> bool:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
                value, _ = winreg.QueryValueEx(key, RUN_VALUE_NAME)
                return bool(value)
        except FileNotFoundError:
            return False
        except OSError:
            LOGGER.exception("Failed to query startup state")
            return False

    def enable(self) -> None:
        command = self._build_launch_command()
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.SetValueEx(key, RUN_VALUE_NAME, 0, winreg.REG_SZ, command)

    def disable(self) -> None:
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.DeleteValue(key, RUN_VALUE_NAME)
        except FileNotFoundError:
            return

    def apply(self, enabled: bool) -> None:
        if enabled:
            self.enable()
        else:
            self.disable()

    def _build_launch_command(self) -> str:
        if getattr(sys, "frozen", False):
            return f'"{Path(sys.executable).resolve()}"'

        pythonw = Path(sys.executable).resolve().with_name("pythonw.exe")
        interpreter = pythonw if pythonw.exists() else Path(sys.executable).resolve()
        script = Path(sys.argv[0]).resolve()
        return f'"{interpreter}" "{script}"'
