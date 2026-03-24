# VolumeSwitch

[English](README.md) | [Chinese](README.zh-CN.md)

`VolumeSwitch` is a Windows 10/11 Python tray utility for quickly switching the default audio output device between two configured targets.

## Features

- Left-click the tray icon to toggle between two preset output devices
- Tray icon changes with the currently active device
- Right-click menu for direct switching, settings, startup toggle, and exit
- First-run configuration stored in a local JSON file
- Global hotkey support
- Single-instance enforcement with activation of the existing instance
- Local log files for troubleshooting

## Requirements

- Windows 11
- Python 3.10 or newer

## DependencyLibrary

```powershell
python -m pip install comtypes
```

## Run

```powershell
python .\VolumeSwitch.py
```

On first launch, the app will ask you to select two audio output devices and will create `volumeswitch_config.json` locally.

## Local Runtime Files

- Config file: `volumeswitch_config.json`
- Log directory: `logs/`


## Project Structure

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
