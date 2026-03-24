from __future__ import annotations

import ctypes
import re
from dataclasses import dataclass
from typing import Optional


MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008

VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_LWIN = 0x5B
VK_RWIN = 0x5C

_user32 = ctypes.windll.user32


@dataclass(frozen=True)
class HotkeyDefinition:
    modifiers: int
    vk: int
    display: str


SPECIAL_KEYS = {
    "SPACE": 0x20,
    "TAB": 0x09,
    "ENTER": 0x0D,
    "RETURN": 0x0D,
    "ESC": 0x1B,
    "ESCAPE": 0x1B,
    "UP": 0x26,
    "DOWN": 0x28,
    "LEFT": 0x25,
    "RIGHT": 0x27,
    "HOME": 0x24,
    "END": 0x23,
    "INSERT": 0x2D,
    "DELETE": 0x2E,
    "PAGEUP": 0x21,
    "PAGEDOWN": 0x22,
}

DISPLAY_ALIASES = {
    0x20: "Space",
    0x09: "Tab",
    0x0D: "Enter",
    0x1B: "Esc",
    0x26: "Up",
    0x28: "Down",
    0x25: "Left",
    0x27: "Right",
    0x24: "Home",
    0x23: "End",
    0x2D: "Insert",
    0x2E: "Delete",
    0x21: "PageUp",
    0x22: "PageDown",
}

MODIFIER_ONLY_VKS = {VK_SHIFT, VK_CONTROL, VK_MENU, VK_LWIN, VK_RWIN}


class HotkeyParseError(ValueError):
    pass


def parse_hotkey(text: str) -> Optional[HotkeyDefinition]:
    value = (text or "").strip()
    if not value:
        return None

    parts = [part.strip() for part in value.split("+") if part.strip()]
    if len(parts) < 2:
        raise HotkeyParseError("全局快捷键至少需要一个修饰键和一个主键。")

    modifiers = 0
    key_part = parts[-1]
    for modifier in parts[:-1]:
        upper = modifier.upper()
        if upper == "CTRL":
            modifiers |= MOD_CONTROL
        elif upper == "ALT":
            modifiers |= MOD_ALT
        elif upper == "SHIFT":
            modifiers |= MOD_SHIFT
        elif upper in {"WIN", "WINDOWS"}:
            modifiers |= MOD_WIN
        else:
            raise HotkeyParseError(f"不支持的修饰键：{modifier}")

    if modifiers == 0:
        raise HotkeyParseError("全局快捷键必须包含 Ctrl、Alt、Shift 或 Win。")

    vk = _parse_key_to_vk(key_part)
    return make_hotkey_definition(modifiers, vk)


def make_hotkey_definition(modifiers: int, vk: int) -> HotkeyDefinition:
    if vk in MODIFIER_ONLY_VKS:
        raise HotkeyParseError("主键不能是单独的修饰键。")
    if modifiers == 0:
        raise HotkeyParseError("全局快捷键必须包含至少一个修饰键。")
    return HotkeyDefinition(modifiers=modifiers, vk=vk, display=format_hotkey(modifiers, vk))


def format_hotkey(modifiers: int, vk: int) -> str:
    parts = []
    if modifiers & MOD_CONTROL:
        parts.append("Ctrl")
    if modifiers & MOD_ALT:
        parts.append("Alt")
    if modifiers & MOD_SHIFT:
        parts.append("Shift")
    if modifiers & MOD_WIN:
        parts.append("Win")
    parts.append(_vk_to_display(vk))
    return "+".join(parts)


def get_pressed_modifiers() -> int:
    modifiers = 0
    if _is_pressed(VK_CONTROL):
        modifiers |= MOD_CONTROL
    if _is_pressed(VK_MENU):
        modifiers |= MOD_ALT
    if _is_pressed(VK_SHIFT):
        modifiers |= MOD_SHIFT
    if _is_pressed(VK_LWIN) or _is_pressed(VK_RWIN):
        modifiers |= MOD_WIN
    return modifiers


def is_modifier_vk(vk: int) -> bool:
    return vk in MODIFIER_ONLY_VKS


def _is_pressed(vk: int) -> bool:
    return bool(_user32.GetKeyState(vk) & 0x8000)


def _parse_key_to_vk(key_part: str) -> int:
    upper = key_part.upper()

    if len(upper) == 1 and upper.isalpha():
        return ord(upper)
    if len(upper) == 1 and upper.isdigit():
        return ord(upper)

    if upper in SPECIAL_KEYS:
        return SPECIAL_KEYS[upper]

    match = re.fullmatch(r"F([1-9]|1[0-9]|2[0-4])", upper)
    if match:
        return 0x70 + int(match.group(1)) - 1

    raise HotkeyParseError(f"不支持的按键：{key_part}")


def _vk_to_display(vk: int) -> str:
    if ord("A") <= vk <= ord("Z"):
        return chr(vk)
    if ord("0") <= vk <= ord("9"):
        return chr(vk)
    if 0x70 <= vk <= 0x87:
        return f"F{vk - 0x70 + 1}"
    return DISPLAY_ALIASES.get(vk, f"VK_{vk}")
