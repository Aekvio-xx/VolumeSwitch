# VolumeSwitch

[English](README.md) | [Chinese](README.zh-CN.md)

`VolumeSwitch` 是一个面向 Windows 10/11 的 Python 托盘小工具，用来在两个预设的音频输出设备之间快速切换。

## 功能

- 左键单击托盘图标即可在两个预设输出设备之间切换
- 托盘图标会根据当前激活设备变化
- 右键菜单支持直接切换、打开设置、切换开机自启和退出
- 首次运行自动生成本地配置文件
- 支持全局快捷键
- 支持单实例运行，重复启动时会唤醒已有实例
- 运行日志写入本地文件，便于排查问题

## 环境要求

- Windows 11
- Python 3.10 或更高版本

## 依赖库

```powershell
python -m pip install comtypes
```

## 运行

```powershell
python .\VolumeSwitch.py
```

首次启动时，程序会提示你选择两个音频输出设备，并在本地生成 `volumeswitch_config.json`。

## 本地运行文件

- 配置文件：`volumeswitch_config.json`
- 日志目录：`logs/`


## 项目结构

```text
VolumeSwitch/
|-- VolumeSwitch.py
|-- README.md
|-- README.zh-CN.md
|-- headset.ico
|-- bspeaker.ico
|-- volumeswitch/
|   |-- __init__.py
|   |-- app.py
|   |-- audio.py
|   |-- config.py
|   |-- hotkey.py
|   |-- logging_utils.py
|   |-- single_instance.py
|   |-- startup.py
|   |-- tray.py
|   `-- ui.py
`-- volumeswitch_config.example.json
```


