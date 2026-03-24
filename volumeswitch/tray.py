from __future__ import annotations

import ctypes
import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from ctypes import wintypes

from .hotkey import HotkeyDefinition


LOGGER = logging.getLogger(__name__)

_user32_dll = ctypes.WinDLL("user32", use_last_error=True)
_shell32_dll = ctypes.WinDLL("shell32", use_last_error=True)
_kernel32_dll = ctypes.WinDLL("kernel32", use_last_error=True)

TRAY_WINDOW_CLASS = "VolumeSwitchTrayWindow"
TRAY_WINDOW_TITLE = "VolumeSwitchTrayWindow"

WM_DESTROY = 0x0002
WM_CLOSE = 0x0010
WM_NULL = 0x0000
WM_COMMAND = 0x0111
WM_CONTEXTMENU = 0x007B
WM_HOTKEY = 0x0312
WM_LBUTTONUP = 0x0202
WM_RBUTTONUP = 0x0205
WM_APP = 0x8000

WMAPP_TRAY_CALLBACK = WM_APP + 1
WMAPP_RELOAD_HOTKEY = WM_APP + 2
WMAPP_SHOW_SETTINGS = WM_APP + 3

NIM_ADD = 0x00000000
NIM_MODIFY = 0x00000001
NIM_DELETE = 0x00000002
NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004
NIF_INFO = 0x00000010
NIIF_INFO = 0x00000001

IMAGE_ICON = 1
LR_LOADFROMFILE = 0x00000010
LR_DEFAULTSIZE = 0x00000040

MF_STRING = 0x0000
MF_SEPARATOR = 0x0800
MF_GRAYED = 0x0001
MF_CHECKED = 0x0008

TPM_RIGHTBUTTON = 0x0002
TPM_RETURNCMD = 0x0100
TPM_NONOTIFY = 0x0080

MENU_CURRENT = 1001
MENU_SWITCH_PRIMARY = 1002
MENU_SWITCH_SECONDARY = 1003
MENU_OPEN_SETTINGS = 1004
MENU_TOGGLE_AUTOSTART = 1005
MENU_EXIT = 1006

HOTKEY_ID = 1

LRESULT = wintypes.LPARAM
WNDPROC = ctypes.WINFUNCTYPE(
    LRESULT,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_ubyte * 8),
    ]


class POINT(ctypes.Structure):
    _fields_ = [
        ("x", wintypes.LONG),
        ("y", wintypes.LONG),
    ]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", POINT),
        ("lPrivate", wintypes.DWORD),
    ]


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HANDLE),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HANDLE),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", wintypes.HANDLE),
        ("szTip", ctypes.c_wchar * 128),
        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),
        ("szInfo", ctypes.c_wchar * 256),
        ("uVersion", wintypes.UINT),
        ("szInfoTitle", ctypes.c_wchar * 64),
        ("dwInfoFlags", wintypes.DWORD),
        ("guidItem", GUID),
        ("hBalloonIcon", wintypes.HANDLE),
    ]


_user32_dll.RegisterWindowMessageW.argtypes = [wintypes.LPCWSTR]
_user32_dll.RegisterWindowMessageW.restype = wintypes.UINT
_user32_dll.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
_user32_dll.RegisterClassW.restype = ctypes.c_ushort
_user32_dll.CreateWindowExW.argtypes = [
    wintypes.DWORD,
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    wintypes.DWORD,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.HWND,
    wintypes.HMENU,
    wintypes.HINSTANCE,
    ctypes.c_void_p,
]
_user32_dll.CreateWindowExW.restype = wintypes.HWND
_user32_dll.DefWindowProcW.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
]
_user32_dll.DefWindowProcW.restype = LRESULT
_user32_dll.DestroyWindow.argtypes = [wintypes.HWND]
_user32_dll.DestroyWindow.restype = wintypes.BOOL
_user32_dll.PostQuitMessage.argtypes = [ctypes.c_int]
_user32_dll.PostQuitMessage.restype = None
_user32_dll.GetMessageW.argtypes = [
    ctypes.POINTER(MSG),
    wintypes.HWND,
    wintypes.UINT,
    wintypes.UINT,
]
_user32_dll.GetMessageW.restype = ctypes.c_int
_user32_dll.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
_user32_dll.TranslateMessage.restype = wintypes.BOOL
_user32_dll.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
_user32_dll.DispatchMessageW.restype = LRESULT
_user32_dll.LoadImageW.argtypes = [
    wintypes.HINSTANCE,
    wintypes.LPCWSTR,
    wintypes.UINT,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.UINT,
]
_user32_dll.LoadImageW.restype = wintypes.HANDLE
_user32_dll.CreatePopupMenu.argtypes = []
_user32_dll.CreatePopupMenu.restype = wintypes.HMENU
_user32_dll.AppendMenuW.argtypes = [
    wintypes.HMENU,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPCWSTR,
]
_user32_dll.AppendMenuW.restype = wintypes.BOOL
_user32_dll.DestroyMenu.argtypes = [wintypes.HMENU]
_user32_dll.DestroyMenu.restype = wintypes.BOOL
_user32_dll.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
_user32_dll.GetCursorPos.restype = wintypes.BOOL
_user32_dll.SetForegroundWindow.argtypes = [wintypes.HWND]
_user32_dll.SetForegroundWindow.restype = wintypes.BOOL
_user32_dll.TrackPopupMenu.argtypes = [
    wintypes.HMENU,
    wintypes.UINT,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.HWND,
    ctypes.c_void_p,
]
_user32_dll.TrackPopupMenu.restype = wintypes.UINT
_user32_dll.PostMessageW.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
]
_user32_dll.PostMessageW.restype = wintypes.BOOL
_user32_dll.RegisterHotKey.argtypes = [
    wintypes.HWND,
    ctypes.c_int,
    wintypes.UINT,
    wintypes.UINT,
]
_user32_dll.RegisterHotKey.restype = wintypes.BOOL
_user32_dll.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
_user32_dll.UnregisterHotKey.restype = wintypes.BOOL
_shell32_dll.Shell_NotifyIconW.argtypes = [
    wintypes.DWORD,
    ctypes.POINTER(NOTIFYICONDATAW),
]
_shell32_dll.Shell_NotifyIconW.restype = wintypes.BOOL


@dataclass
class TrayState:
    current_name: str = "未配置"
    current_slot: str = "unknown"
    primary_name: str = "耳机"
    secondary_name: str = "扬声器"
    autostart_enabled: bool = False
    configured: bool = False


@dataclass
class HotkeyRequest:
    definition: Optional[HotkeyDefinition]
    done: threading.Event
    success: bool = False
    error_message: str = ""


class WinTrayController:
    def __init__(
        self,
        command_queue: "queue.Queue[tuple[str, str | None]]",
        icon_headset: Path,
        icon_speaker: Path,
    ) -> None:
        self.command_queue = command_queue
        self.icon_headset = icon_headset
        self.icon_speaker = icon_speaker

        self._thread: Optional[threading.Thread] = None
        self._ready = threading.Event()
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._state = TrayState()
        self._hwnd = None
        self._wndproc = None
        self._headset_hicon = None
        self._speaker_hicon = None
        self._current_hotkey: Optional[HotkeyDefinition] = None
        self._pending_hotkey_request: Optional[HotkeyRequest] = None
        self._taskbar_created = _user32_dll.RegisterWindowMessageW("TaskbarCreated")

        self._user32 = _user32_dll
        self._shell32 = _shell32_dll
        self._kernel32 = _kernel32_dll

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._thread = threading.Thread(
            target=self._thread_main,
            name="VolumeSwitchTray",
            daemon=True,
        )
        self._thread.start()
        if not self._ready.wait(timeout=5):
            raise RuntimeError("托盘线程启动超时。")

    def stop(self) -> None:
        self._stop_event.set()
        if self._hwnd:
            self._user32.PostMessageW(self._hwnd, WM_CLOSE, 0, 0)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)

    def update_state(self, state: TrayState) -> None:
        with self._lock:
            self._state = state
        self._refresh_icon_and_tooltip()

    def show_notification(self, title: str, message: str) -> None:
        if not self._hwnd:
            return
        nid = self._build_notify_data(
            flags=NIF_INFO,
            info_title=title,
            info_text=message,
        )
        self._shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid))

    def configure_hotkey(
        self, definition: Optional[HotkeyDefinition]
    ) -> tuple[bool, str]:
        if not self._hwnd:
            return False, "托盘尚未就绪。"

        request = HotkeyRequest(definition=definition, done=threading.Event())
        with self._lock:
            self._pending_hotkey_request = request
        self._user32.PostMessageW(self._hwnd, WMAPP_RELOAD_HOTKEY, 0, 0)
        if not request.done.wait(timeout=3):
            return False, "快捷键注册超时。"
        return request.success, request.error_message

    def _thread_main(self) -> None:
        try:
            self._register_window_class()
            self._create_window()
            self._load_icons()
            self._add_tray_icon()
            self._ready.set()
            self._message_loop()
        except Exception:
            LOGGER.exception("Tray thread crashed")
            self.command_queue.put(("fatal_error", "托盘初始化失败。"))
            self._ready.set()
        finally:
            self._destroy_icons()

    def _register_window_class(self) -> None:
        self._wndproc = WNDPROC(self._window_proc)

        wndclass = WNDCLASSW()
        wndclass.lpfnWndProc = self._wndproc
        wndclass.hInstance = self._kernel32.GetModuleHandleW(None)
        wndclass.lpszClassName = TRAY_WINDOW_CLASS

        atom = self._user32.RegisterClassW(ctypes.byref(wndclass))
        if not atom and ctypes.get_last_error() != 1410:
            raise ctypes.WinError()

    def _create_window(self) -> None:
        self._hwnd = self._user32.CreateWindowExW(
            0,
            TRAY_WINDOW_CLASS,
            TRAY_WINDOW_TITLE,
            0,
            0,
            0,
            0,
            0,
            None,
            None,
            self._kernel32.GetModuleHandleW(None),
            None,
        )
        if not self._hwnd:
            raise ctypes.WinError()

    def _load_icons(self) -> None:
        self._headset_hicon = self._load_icon(self.icon_headset)
        self._speaker_hicon = self._load_icon(self.icon_speaker)

    def _load_icon(self, path: Path):
        if not path.exists():
            return None
        return self._user32.LoadImageW(
            None,
            str(path),
            IMAGE_ICON,
            0,
            0,
            LR_LOADFROMFILE | LR_DEFAULTSIZE,
        )

    def _add_tray_icon(self) -> None:
        nid = self._build_notify_data(
            flags=NIF_MESSAGE | NIF_ICON | NIF_TIP,
            tooltip=self._build_tooltip_text(),
        )
        if not self._shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid)):
            raise RuntimeError("无法创建系统托盘图标。")

    def _remove_tray_icon(self) -> None:
        if not self._hwnd:
            return
        nid = self._build_notify_data(flags=0)
        self._shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid))

    def _refresh_icon_and_tooltip(self) -> None:
        if not self._hwnd:
            return
        nid = self._build_notify_data(
            flags=NIF_ICON | NIF_TIP,
            tooltip=self._build_tooltip_text(),
        )
        self._shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid))

    def _build_tooltip_text(self) -> str:
        with self._lock:
            current_name = self._state.current_name
        return f"当前输出：{current_name}"[:127]

    def _build_notify_data(
        self,
        flags: int,
        tooltip: str = "",
        info_title: str = "",
        info_text: str = "",
    ) -> NOTIFYICONDATAW:
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self._hwnd
        nid.uID = 1
        nid.uFlags = flags
        nid.uCallbackMessage = WMAPP_TRAY_CALLBACK
        nid.hIcon = self._pick_icon_handle()
        if tooltip:
            nid.szTip = tooltip[:127]
        if info_text:
            nid.szInfo = info_text[:255]
            nid.szInfoTitle = info_title[:63]
            nid.dwInfoFlags = NIIF_INFO
        return nid

    def _pick_icon_handle(self):
        with self._lock:
            current_slot = self._state.current_slot
        if current_slot == "secondary" and self._speaker_hicon:
            return self._speaker_hicon
        return self._headset_hicon or self._speaker_hicon

    def _message_loop(self) -> None:
        msg = MSG()
        while not self._stop_event.is_set():
            result = self._user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if result == -1:
                raise ctypes.WinError()
            if result == 0:
                break
            self._user32.TranslateMessage(ctypes.byref(msg))
            self._user32.DispatchMessageW(ctypes.byref(msg))

    def _window_proc(self, hwnd, msg, wparam, lparam):
        try:
            if msg == self._taskbar_created:
                self._add_tray_icon()
                self._refresh_icon_and_tooltip()
                return 0
            if msg == WMAPP_TRAY_CALLBACK:
                return self._handle_tray_event(lparam)
            if msg == WMAPP_RELOAD_HOTKEY:
                self._handle_hotkey_request()
                return 0
            if msg == WMAPP_SHOW_SETTINGS:
                self.command_queue.put(("show_settings", None))
                return 0
            if msg == WM_HOTKEY and wparam == HOTKEY_ID:
                self.command_queue.put(("toggle", None))
                return 0
            if msg == WM_COMMAND:
                self._dispatch_menu_command(wparam & 0xFFFF)
                return 0
            if msg == WM_CLOSE:
                self._remove_tray_icon()
                self._user32.DestroyWindow(hwnd)
                return 0
            if msg == WM_DESTROY:
                self._user32.PostQuitMessage(0)
                return 0
        except Exception:
            LOGGER.exception("Tray window proc error")
        return self._user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _handle_tray_event(self, lparam: int) -> int:
        if lparam == WM_LBUTTONUP:
            self.command_queue.put(("toggle", None))
            return 0
        if lparam in (WM_RBUTTONUP, WM_CONTEXTMENU):
            self._show_context_menu()
            return 0
        return 0

    def _show_context_menu(self) -> None:
        menu = self._user32.CreatePopupMenu()
        if not menu:
            return

        try:
            with self._lock:
                state = self._state

            current_label = f"当前输出：{state.current_name}"
            self._user32.AppendMenuW(menu, MF_STRING | MF_GRAYED, MENU_CURRENT, current_label)
            self._user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)

            primary_label = f"切换到耳机（{state.primary_name or '未配置'}）"
            secondary_label = f"切换到扬声器（{state.secondary_name or '未配置'}）"
            device_flags = MF_STRING if state.configured else MF_STRING | MF_GRAYED
            self._user32.AppendMenuW(menu, device_flags, MENU_SWITCH_PRIMARY, primary_label)
            self._user32.AppendMenuW(menu, device_flags, MENU_SWITCH_SECONDARY, secondary_label)
            self._user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
            self._user32.AppendMenuW(menu, MF_STRING, MENU_OPEN_SETTINGS, "打开设置")

            autostart_flags = MF_STRING | (MF_CHECKED if state.autostart_enabled else 0)
            self._user32.AppendMenuW(menu, autostart_flags, MENU_TOGGLE_AUTOSTART, "开机自启动")
            self._user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
            self._user32.AppendMenuW(menu, MF_STRING, MENU_EXIT, "退出")

            cursor = POINT()
            self._user32.GetCursorPos(ctypes.byref(cursor))
            self._user32.SetForegroundWindow(self._hwnd)
            selected = self._user32.TrackPopupMenu(
                menu,
                TPM_RIGHTBUTTON | TPM_RETURNCMD | TPM_NONOTIFY,
                cursor.x,
                cursor.y,
                0,
                self._hwnd,
                None,
            )
            if selected:
                self._dispatch_menu_command(selected)
            self._user32.PostMessageW(self._hwnd, WM_NULL, 0, 0)
        finally:
            self._user32.DestroyMenu(menu)

    def _dispatch_menu_command(self, command_id: int) -> None:
        if command_id == MENU_SWITCH_PRIMARY:
            self.command_queue.put(("switch_primary", None))
        elif command_id == MENU_SWITCH_SECONDARY:
            self.command_queue.put(("switch_secondary", None))
        elif command_id == MENU_OPEN_SETTINGS:
            self.command_queue.put(("show_settings", None))
        elif command_id == MENU_TOGGLE_AUTOSTART:
            self.command_queue.put(("toggle_autostart", None))
        elif command_id == MENU_EXIT:
            self.command_queue.put(("quit", None))

    def _handle_hotkey_request(self) -> None:
        with self._lock:
            request = self._pending_hotkey_request
            self._pending_hotkey_request = None

        if not request:
            return

        previous = self._current_hotkey
        if previous:
            self._user32.UnregisterHotKey(self._hwnd, HOTKEY_ID)

        success = True
        error_message = ""
        if request.definition:
            if self._user32.RegisterHotKey(
                self._hwnd,
                HOTKEY_ID,
                request.definition.modifiers,
                request.definition.vk,
            ):
                self._current_hotkey = request.definition
            else:
                success = False
                error_message = "快捷键已被其他程序占用或注册失败。"
                self._current_hotkey = None
                if previous:
                    if self._user32.RegisterHotKey(
                        self._hwnd,
                        HOTKEY_ID,
                        previous.modifiers,
                        previous.vk,
                    ):
                        self._current_hotkey = previous
        else:
            self._current_hotkey = None

        request.success = success
        request.error_message = error_message
        request.done.set()

    def _destroy_icons(self) -> None:
        for icon_handle in (self._headset_hicon, self._speaker_hicon):
            if icon_handle:
                self._user32.DestroyIcon(icon_handle)
