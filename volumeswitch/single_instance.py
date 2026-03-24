from __future__ import annotations

import ctypes
import logging
import time


LOGGER = logging.getLogger(__name__)

TRAY_WINDOW_CLASS = "VolumeSwitchTrayWindow"
TRAY_WINDOW_TITLE = "VolumeSwitchTrayWindow"
WM_APP = 0x8000
WMAPP_SHOW_SETTINGS = WM_APP + 3

_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_user32 = ctypes.WinDLL("user32", use_last_error=True)
ERROR_ALREADY_EXISTS = 183


class SingleInstance:
    MUTEX_NAME = "Local\\VolumeSwitch.SingleInstance"

    def __init__(self) -> None:
        self._mutex = None

    def acquire(self) -> bool:
        self._mutex = _kernel32.CreateMutexW(None, False, self.MUTEX_NAME)
        last_error = ctypes.get_last_error()
        return bool(self._mutex) and last_error != ERROR_ALREADY_EXISTS

    def release(self) -> None:
        if self._mutex:
            _kernel32.CloseHandle(self._mutex)
            self._mutex = None

    @staticmethod
    def signal_existing_instance() -> bool:
        for _ in range(15):
            hwnd = _user32.FindWindowW(TRAY_WINDOW_CLASS, TRAY_WINDOW_TITLE)
            if hwnd:
                _user32.PostMessageW(hwnd, WMAPP_SHOW_SETTINGS, 0, 0)
                return True
            time.sleep(0.2)
        LOGGER.warning("Existing instance was not found after duplicate launch")
        return False
