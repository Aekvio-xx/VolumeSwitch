from __future__ import annotations

import copy
import logging
import queue
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import Optional

from . import APP_NAME
from .audio import AudioController
from .config import AppConfig, ConfigManager, DeviceConfig
from .hotkey import HotkeyParseError, parse_hotkey
from .single_instance import SingleInstance
from .startup import StartupManager
from .tray import TrayState, WinTrayController
from .ui import SettingsWindow


def main() -> int:
    app_dir = get_app_dir()
    from .logging_utils import install_exception_hooks, setup_logging

    setup_logging(app_dir)
    install_exception_hooks()
    logger = logging.getLogger("volumeswitch")

    instance = SingleInstance()
    if not instance.acquire():
        logger.info("Duplicate instance detected, activating existing instance")
        SingleInstance.signal_existing_instance()
        return 0

    app: Optional[VolumeSwitchApp] = None
    try:
        app = VolumeSwitchApp(app_dir=app_dir, instance=instance)
        return app.run()
    except Exception:
        logger.exception("Application startup failed")
        if app is not None:
            try:
                app.shutdown()
            except Exception:
                logger.exception("Application shutdown after startup failure failed")
        try:
            messagebox.showerror(APP_NAME, "程序启动失败，请查看日志文件。")
        except Exception:
            pass
        return 1
    finally:
        if app is not None:
            app.release_single_instance()
        else:
            instance.release()


def get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_resource_dir() -> Path:
    frozen_bundle_dir = getattr(sys, "_MEIPASS", None)
    if frozen_bundle_dir:
        return Path(frozen_bundle_dir)
    return Path(__file__).resolve().parent.parent


class VolumeSwitchApp:
    def __init__(self, app_dir: Path, instance: SingleInstance) -> None:
        self.app_dir = app_dir
        self.resource_dir = get_resource_dir()
        self.logger = logging.getLogger("volumeswitch")
        self.instance = instance

        self.command_queue: queue.Queue[tuple[str, str | None]] = queue.Queue()
        self.audio = AudioController()
        self.startup = StartupManager()
        self.config_manager = ConfigManager(app_dir)
        self.config = self.config_manager.load()
        actual_autostart = self.startup.is_enabled()
        if self.config.autostart != actual_autostart:
            self.config.autostart = actual_autostart
            try:
                self.config_manager.save(self.config)
            except Exception:
                self.logger.exception("Failed to sync autostart state into config")

        self.devices = []
        self.devices_by_id = {}

        self.root = tk.Tk()
        self.root.withdraw()
        self.root.report_callback_exception = self._handle_tk_exception

        self.settings_window = SettingsWindow(
            self.root,
            on_save=self.save_settings,
            on_refresh=self.refresh_devices_from_ui,
            on_test=self.test_switch,
        )
        self.tray = WinTrayController(
            command_queue=self.command_queue,
            icon_headset=self.resource_dir / "headset.ico",
            icon_speaker=self.resource_dir / "bspeaker.ico",
        )
        self._running = True

        try:
            self.audio.register_default_output_listener(
                self._queue_default_output_change
            )
        except Exception:
            self.logger.exception("Failed to register default output listener")

    def run(self) -> int:
        self.tray.start()
        self.refresh_devices()
        self._apply_hotkey_on_startup()
        self.root.after(100, self._process_commands)

        if not self.config.is_complete:
            self.show_settings()
            self._notify("首次运行", "请先在设置中选择耳机和扬声器设备。", force=True)
        elif not self.config.start_minimized:
            self.show_settings()

        self.root.mainloop()
        return 0

    def release_single_instance(self) -> None:
        self.instance.release()

    def shutdown(self) -> None:
        if not self._running:
            return
        self._running = False

        try:
            self.tray.stop()
        except Exception:
            self.logger.exception("Failed to stop tray")

        try:
            self.audio.close()
        except Exception:
            self.logger.exception("Failed to close audio controller")

        self.root.quit()
        self.root.destroy()

    def refresh_devices(self) -> None:
        self.devices = [
            {"id": item.id, "name": item.name}
            for item in self.audio.list_render_devices()
        ]
        self.devices_by_id = {item["id"]: item for item in self.devices}
        self._refresh_tray_state()
        if self.settings_window.has_window():
            self.settings_window.update_form(
                self.config,
                self.devices,
                self._get_current_output_name(),
            )

    def refresh_devices_from_ui(self) -> None:
        current_form = self.settings_window.get_form_data()
        self.refresh_devices()
        self.settings_window.set_selected_ids(
            current_form["primary_id"],
            current_form["secondary_id"],
        )

    def show_settings(self) -> None:
        self.refresh_devices()
        self.settings_window.show(
            self.config,
            self.devices,
            self._get_current_output_name(),
        )

    def save_settings(self, form_data: dict) -> None:
        try:
            self._validate_form(form_data)
            new_config = self._build_config_from_form(form_data)
            self._commit_settings(new_config)
            self._refresh_tray_state()
            self.settings_window.hide()
            self._notify("设置已保存", "新的设备配置已生效。", force=True)
        except Exception as exc:
            self.logger.exception("Failed to save settings")
            messagebox.showerror(APP_NAME, str(exc))

    def test_switch(self, form_data: dict) -> None:
        try:
            self._validate_form(form_data)
            current_id = self.audio.get_default_output_device_id()
            primary_id = form_data["primary_id"]
            secondary_id = form_data["secondary_id"]
            target_id = secondary_id if current_id == primary_id else primary_id
            self.audio.set_default_output_device(target_id)
            self._refresh_tray_state()
        except Exception as exc:
            self.logger.exception("Test switch failed")
            messagebox.showerror(APP_NAME, str(exc))

    def toggle_output(self) -> None:
        self.refresh_devices()
        self._ensure_configured_devices_available()

        current_id = self.audio.get_default_output_device_id()
        if current_id == self.config.primary.id:
            target = self.config.secondary
        elif current_id == self.config.secondary.id:
            target = self.config.primary
        else:
            target = (
                self.config.primary
                if self.config.fallback_to_primary_on_unknown
                else self.config.secondary
            )

        self._switch_to_device(target)

    def switch_to_primary(self) -> None:
        self.refresh_devices()
        self._ensure_configured_devices_available()
        self._switch_to_device(self.config.primary)

    def switch_to_secondary(self) -> None:
        self.refresh_devices()
        self._ensure_configured_devices_available()
        self._switch_to_device(self.config.secondary)

    def toggle_autostart(self) -> None:
        desired = not self.config.autostart
        try:
            self.startup.apply(desired)
            self.config.autostart = desired
            self.config_manager.save(self.config)
            self._refresh_tray_state()
            self._notify(
                "开机自启动",
                "已开启开机自启动。" if desired else "已关闭开机自启动。",
                force=True,
            )
            if self.settings_window.has_window():
                self.settings_window.autostart_var.set(desired)
        except Exception:
            self.logger.exception("Failed to toggle autostart")
            messagebox.showerror(APP_NAME, "切换开机自启动失败，请查看日志。")

    def _process_commands(self) -> None:
        while True:
            try:
                command, payload = self.command_queue.get_nowait()
            except queue.Empty:
                break

            try:
                self._handle_command(command, payload)
            except Exception:
                self.logger.exception("Command handling failed: %s", command)
                self._notify("操作失败", "执行命令时发生异常，请查看日志。", force=True)

        if self._running:
            self.root.after(100, self._process_commands)

    def _handle_command(self, command: str, payload: str | None) -> None:
        if command == "toggle":
            self.toggle_output()
        elif command == "default_output_changed":
            self._refresh_tray_state()
        elif command == "switch_primary":
            self.switch_to_primary()
        elif command == "switch_secondary":
            self.switch_to_secondary()
        elif command == "show_settings":
            self.show_settings()
        elif command == "toggle_autostart":
            self.toggle_autostart()
        elif command == "quit":
            self.shutdown()
        elif command == "fatal_error":
            messagebox.showerror(APP_NAME, str(payload))
            self.shutdown()

    def _refresh_tray_state(self) -> None:
        current_id = None
        try:
            current_id = self.audio.get_default_output_device_id()
        except Exception:
            self.logger.exception("Failed to read current default output")

        current_name = self._resolve_device_name(current_id) or "未知设备"
        current_slot = "unknown"
        if current_id == self.config.primary.id:
            current_slot = "primary"
        elif current_id == self.config.secondary.id:
            current_slot = "secondary"

        state = TrayState(
            current_name=current_name,
            current_slot=current_slot,
            primary_name=self.config.primary.name or "耳机",
            secondary_name=self.config.secondary.name or "扬声器",
            autostart_enabled=self.config.autostart,
            configured=self.config.is_complete,
        )
        self.tray.update_state(state)

        if self.settings_window.has_window():
            self.settings_window.current_output_var.set(f"当前输出：{current_name}")

    def _resolve_device_name(self, device_id: Optional[str]) -> str:
        if not device_id:
            return ""
        if device_id == self.config.primary.id and self.config.primary.name:
            return self.config.primary.name
        if device_id == self.config.secondary.id and self.config.secondary.name:
            return self.config.secondary.name
        if device_id in self.devices_by_id:
            return self.devices_by_id[device_id]["name"]
        device = self.audio.get_device_by_id(device_id)
        return device.name if device else ""

    def _get_current_output_name(self) -> str:
        try:
            device_id = self.audio.get_default_output_device_id()
            return self._resolve_device_name(device_id) or "未知设备"
        except Exception:
            self.logger.exception("Failed to get current output name")
            return "未知设备"

    def _switch_to_device(self, device: DeviceConfig) -> None:
        if not device.id:
            raise ValueError("目标设备未配置。")
        if device.id not in self.devices_by_id:
            raise ValueError(f"配置的设备不存在：{device.name or device.id}")

        self.audio.set_default_output_device(device.id)
        self._refresh_tray_state()

    def _ensure_configured_devices_available(self) -> None:
        if not self.config.is_complete:
            self.show_settings()
            raise ValueError("请先在设置中选择耳机和扬声器设备。")
        if not self.devices:
            raise ValueError("当前没有可用的音频输出设备。")
        missing = []
        if self.config.primary.id not in self.devices_by_id:
            missing.append(self.config.primary.name or "耳机")
        if self.config.secondary.id not in self.devices_by_id:
            missing.append(self.config.secondary.name or "扬声器")
        if missing:
            self.show_settings()
            raise ValueError(f"以下配置设备当前不可用：{'、'.join(missing)}")

    def _validate_form(self, form_data: dict) -> None:
        primary_id = form_data.get("primary_id", "")
        secondary_id = form_data.get("secondary_id", "")

        if not primary_id or not secondary_id:
            raise ValueError("请先选择耳机和扬声器设备。")
        if primary_id == secondary_id:
            raise ValueError("耳机和扬声器不能选择同一个设备。")
        if primary_id not in self.devices_by_id or secondary_id not in self.devices_by_id:
            raise ValueError("所选设备已失效，请刷新设备列表后重新选择。")

        hotkey = (form_data.get("hotkey") or "").strip()
        if hotkey:
            parse_hotkey(hotkey)

    def _build_config_from_form(self, form_data: dict) -> AppConfig:
        primary_id = form_data["primary_id"]
        secondary_id = form_data["secondary_id"]

        return AppConfig(
            primary=DeviceConfig(
                id=primary_id,
                name=self.devices_by_id[primary_id]["name"],
            ),
            secondary=DeviceConfig(
                id=secondary_id,
                name=self.devices_by_id[secondary_id]["name"],
            ),
            hotkey=(form_data.get("hotkey") or "").strip(),
            autostart=bool(form_data.get("autostart")),
            start_minimized=bool(form_data.get("start_minimized")),
            show_notifications=bool(form_data.get("show_notifications")),
            fallback_to_primary_on_unknown=True,
        )

    def _commit_settings(self, new_config: AppConfig) -> None:
        old_config = copy.deepcopy(self.config)
        old_hotkey = parse_hotkey(old_config.hotkey) if old_config.hotkey else None
        new_hotkey = parse_hotkey(new_config.hotkey) if new_config.hotkey else None

        if old_config.hotkey != new_config.hotkey:
            success, error_message = self.tray.configure_hotkey(new_hotkey)
            if not success:
                raise ValueError(error_message)

        try:
            self.startup.apply(new_config.autostart)
        except Exception:
            if old_config.hotkey != new_config.hotkey:
                self.tray.configure_hotkey(old_hotkey)
            raise ValueError("设置开机自启动失败。")

        try:
            self.config = new_config
            self.config_manager.save(self.config)
        except Exception:
            self.config = old_config
            self.startup.apply(old_config.autostart)
            if old_config.hotkey != new_config.hotkey:
                self.tray.configure_hotkey(old_hotkey)
            raise ValueError("保存配置文件失败。")

    def _apply_hotkey_on_startup(self) -> None:
        if not self.config.hotkey:
            return
        try:
            definition = parse_hotkey(self.config.hotkey)
        except HotkeyParseError as exc:
            self.logger.warning("Invalid hotkey in config: %s", exc)
            self._notify("快捷键无效", "配置中的快捷键格式无效，请重新设置。", force=True)
            return

        success, error_message = self.tray.configure_hotkey(definition)
        if not success:
            self.logger.warning("Failed to register startup hotkey: %s", error_message)
            self._notify("快捷键注册失败", error_message, force=True)

    def _notify(self, title: str, message: str, force: bool = False) -> None:
        if force or self.config.show_notifications:
            self.tray.show_notification(title, message)

    def _queue_default_output_change(self, _device_id: str) -> None:
        if self._running:
            self.command_queue.put(("default_output_changed", None))

    def _handle_tk_exception(self, exc_type, exc_value, exc_traceback) -> None:
        self.logger.exception(
            "Tkinter callback exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )
        self._notify("界面异常", "界面操作失败，请查看日志。", force=True)
