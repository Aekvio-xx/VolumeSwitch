from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, List, Optional

from .config import AppConfig
from .hotkey import (
    HotkeyParseError,
    get_pressed_modifiers,
    is_modifier_vk,
    make_hotkey_definition,
)


class SettingsWindow:
    def __init__(
        self,
        root: tk.Tk,
        on_save: Callable[[dict], None],
        on_refresh: Callable[[], None],
        on_test: Callable[[dict], None],
    ) -> None:
        self.root = root
        self.on_save = on_save
        self.on_refresh = on_refresh
        self.on_test = on_test

        self.window: Optional[tk.Toplevel] = None
        self._capture_active = False
        self._device_display_to_id: Dict[str, str] = {}
        self._id_to_display: Dict[str, str] = {}

        self.current_output_var = tk.StringVar(value="当前输出：未知")
        self.primary_var = tk.StringVar()
        self.secondary_var = tk.StringVar()
        self.hotkey_var = tk.StringVar()
        self.autostart_var = tk.BooleanVar(value=False)
        self.start_minimized_var = tk.BooleanVar(value=True)
        self.notify_var = tk.BooleanVar(value=True)
        self.capture_hint_var = tk.StringVar(
            value="点击“录制快捷键”，然后按下组合键。按 Esc 清空。"
        )

    def show(
        self,
        config: AppConfig,
        devices: List[dict],
        current_output_name: str,
    ) -> None:
        if not self.window or not self.window.winfo_exists():
            self._build()
        self.update_form(config, devices, current_output_name)
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()
        self.window.attributes("-topmost", True)
        self.window.after(200, lambda: self.window.attributes("-topmost", False))

    def hide(self) -> None:
        if self.window and self.window.winfo_exists():
            self._stop_capture()
            self.window.withdraw()

    def update_form(
        self,
        config: AppConfig,
        devices: List[dict],
        current_output_name: str,
    ) -> None:
        self.set_devices(devices)
        self.current_output_var.set(f"当前输出：{current_output_name}")
        self.primary_var.set(self._id_to_display.get(config.primary.id, ""))
        self.secondary_var.set(self._id_to_display.get(config.secondary.id, ""))
        self.hotkey_var.set(config.hotkey)
        self.autostart_var.set(config.autostart)
        self.start_minimized_var.set(config.start_minimized)
        self.notify_var.set(config.show_notifications)

    def set_devices(self, devices: List[dict]) -> None:
        self._device_display_to_id.clear()
        self._id_to_display.clear()

        names = {}
        for item in devices:
            names[item["name"]] = names.get(item["name"], 0) + 1

        display_values = []
        for item in devices:
            if names[item["name"]] > 1:
                display = f'{item["name"]}  [{item["id"][-8:]}]'
            else:
                display = item["name"]
            self._device_display_to_id[display] = item["id"]
            self._id_to_display[item["id"]] = display
            display_values.append(display)

        if self.window and self.window.winfo_exists():
            self.primary_combo["values"] = display_values
            self.secondary_combo["values"] = display_values

    def get_form_data(self) -> dict:
        return {
            "primary_id": self._device_display_to_id.get(self.primary_var.get(), ""),
            "secondary_id": self._device_display_to_id.get(self.secondary_var.get(), ""),
            "hotkey": self.hotkey_var.get().strip(),
            "autostart": self.autostart_var.get(),
            "start_minimized": self.start_minimized_var.get(),
            "show_notifications": self.notify_var.get(),
        }

    def has_window(self) -> bool:
        return bool(self.window and self.window.winfo_exists())

    def set_selected_ids(self, primary_id: str, secondary_id: str) -> None:
        self.primary_var.set(self._id_to_display.get(primary_id, ""))
        self.secondary_var.set(self._id_to_display.get(secondary_id, ""))

    def _build(self) -> None:
        self.window = tk.Toplevel(self.root)
        self.window.title("VolumeSwitch 设置")
        self.window.geometry("520x330")
        self.window.resizable(False, False)
        self.window.protocol("WM_DELETE_WINDOW", self.hide)
        self.window.bind("<KeyPress>", self._capture_hotkey, add="+")

        frame = ttk.Frame(self.window, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, textvariable=self.current_output_var).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 12)
        )

        ttk.Label(frame, text="耳机设备").grid(row=1, column=0, sticky="w", pady=6)
        self.primary_combo = ttk.Combobox(
            frame,
            textvariable=self.primary_var,
            state="readonly",
            width=42,
        )
        self.primary_combo.grid(row=1, column=1, columnspan=2, sticky="ew", pady=6)

        ttk.Label(frame, text="扬声器设备").grid(row=2, column=0, sticky="w", pady=6)
        self.secondary_combo = ttk.Combobox(
            frame,
            textvariable=self.secondary_var,
            state="readonly",
            width=42,
        )
        self.secondary_combo.grid(row=2, column=1, columnspan=2, sticky="ew", pady=6)

        ttk.Label(frame, text="全局快捷键").grid(row=3, column=0, sticky="w", pady=6)
        hotkey_entry = ttk.Entry(
            frame,
            textvariable=self.hotkey_var,
            state="readonly",
            width=24,
        )
        hotkey_entry.grid(row=3, column=1, sticky="ew", pady=6)
        ttk.Button(
            frame,
            text="录制快捷键",
            command=self._start_capture,
            width=12,
        ).grid(row=3, column=2, sticky="e", pady=6)

        ttk.Label(frame, textvariable=self.capture_hint_var, foreground="#666666").grid(
            row=4, column=0, columnspan=3, sticky="w", pady=(0, 12)
        )

        ttk.Checkbutton(
            frame,
            text="开机自启动",
            variable=self.autostart_var,
        ).grid(row=5, column=0, sticky="w", pady=4)
        ttk.Checkbutton(
            frame,
            text="启动时最小化到托盘",
            variable=self.start_minimized_var,
        ).grid(row=5, column=1, sticky="w", pady=4)
        ttk.Checkbutton(
            frame,
            text="切换后显示通知",
            variable=self.notify_var,
        ).grid(row=5, column=2, sticky="w", pady=4)

        button_bar = ttk.Frame(frame)
        button_bar.grid(row=6, column=0, columnspan=3, sticky="e", pady=(20, 0))

        ttk.Button(button_bar, text="刷新设备列表", command=self.on_refresh).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(
            button_bar,
            text="测试切换",
            command=lambda: self.on_test(self.get_form_data()),
        ).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(
            button_bar,
            text="保存",
            command=lambda: self.on_save(self.get_form_data()),
        ).pack(side=tk.LEFT)

    def _start_capture(self) -> None:
        self._capture_active = True
        self.capture_hint_var.set("请按下组合键。按 Esc 可清空快捷键。")
        if self.window and self.window.winfo_exists():
            self.window.focus_force()

    def _stop_capture(self) -> None:
        self._capture_active = False
        self.capture_hint_var.set(
            "点击“录制快捷键”，然后按下组合键。按 Esc 清空。"
        )

    def _capture_hotkey(self, event) -> str | None:
        if not self._capture_active:
            return None

        vk = int(event.keycode)
        if is_modifier_vk(vk):
            return "break"

        modifiers = get_pressed_modifiers()
        if vk == 0x1B and modifiers == 0:
            self.hotkey_var.set("")
            self._stop_capture()
            return "break"

        try:
            definition = make_hotkey_definition(modifiers, vk)
        except HotkeyParseError:
            self.capture_hint_var.set("快捷键至少需要一个修饰键和一个主键。")
            return "break"

        self.hotkey_var.set(definition.display)
        self._stop_capture()
        return "break"
