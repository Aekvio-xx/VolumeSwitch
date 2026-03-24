from __future__ import annotations

import ctypes
import logging
from dataclasses import dataclass
from typing import Callable, List, Optional

import comtypes
from comtypes import COMMETHOD, COMObject, GUID, HRESULT, IUnknown
from ctypes import POINTER, Structure, Union, byref, c_ulonglong, c_void_p, wintypes


LOGGER = logging.getLogger(__name__)

ole32 = ctypes.windll.ole32

CLSCTX_ALL = comtypes.CLSCTX_ALL
STGM_READ = 0x00000000
DEVICE_STATE_ACTIVE = 0x00000001
ERENDER = 0
ROLE_CONSOLE = 0
ROLE_MULTIMEDIA = 1
ROLE_COMMUNICATIONS = 2
VT_LPWSTR = 31


class PROPERTYKEY(Structure):
    _fields_ = [
        ("fmtid", GUID),
        ("pid", wintypes.DWORD),
    ]


class PROPVARIANT_UNION(Union):
    _fields_ = [
        ("pwszVal", wintypes.LPWSTR),
        ("uhVal", c_ulonglong),
        ("punkVal", c_void_p),
    ]


class PROPVARIANT(Structure):
    _fields_ = [
        ("vt", wintypes.USHORT),
        ("wReserved1", wintypes.USHORT),
        ("wReserved2", wintypes.USHORT),
        ("wReserved3", wintypes.USHORT),
        ("data", PROPVARIANT_UNION),
    ]


class IPropertyStore(IUnknown):
    _iid_ = GUID("{886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99}")


class IMMDevice(IUnknown):
    _iid_ = GUID("{D666063F-1587-4E43-81F1-B948E807363F}")


class IMMDeviceCollection(IUnknown):
    _iid_ = GUID("{0BD7A1BE-7A1A-44DB-8397-C0A7C3D62F4D}")


class IMMDeviceEnumerator(IUnknown):
    _iid_ = GUID("{A95664D2-9614-4F35-A746-DE8DB63617E6}")


class IMMNotificationClient(IUnknown):
    _iid_ = GUID("{7991EEC9-7E89-4D85-8390-6C703CEC60C0}")


class IPolicyConfig(IUnknown):
    _iid_ = GUID("{F8679F50-850A-41CF-9C72-430F290290C8}")


IPropertyStore._methods_ = [
    COMMETHOD([], HRESULT, "GetCount", (["out"], POINTER(wintypes.DWORD), "cProps")),
    COMMETHOD([], HRESULT, "GetAt", (["in"], wintypes.DWORD, "iProp"), (["out"], POINTER(PROPERTYKEY), "pkey")),
    COMMETHOD([], HRESULT, "GetValue", (["in"], POINTER(PROPERTYKEY), "key"), (["out"], POINTER(PROPVARIANT), "pv")),
    COMMETHOD([], HRESULT, "SetValue", (["in"], POINTER(PROPERTYKEY), "key"), (["in"], POINTER(PROPVARIANT), "propvar")),
    COMMETHOD([], HRESULT, "Commit"),
]

IMMDevice._methods_ = [
    COMMETHOD([], HRESULT, "Activate", (["in"], POINTER(GUID), "iid"), (["in"], wintypes.DWORD, "dwClsCtx"), (["in"], c_void_p, "pActivationParams"), (["out"], POINTER(c_void_p), "ppInterface")),
    COMMETHOD([], HRESULT, "OpenPropertyStore", (["in"], wintypes.DWORD, "stgmAccess"), (["out"], POINTER(POINTER(IPropertyStore)), "ppProperties")),
    COMMETHOD([], HRESULT, "GetId", (["out"], POINTER(wintypes.LPWSTR), "ppstrId")),
    COMMETHOD([], HRESULT, "GetState", (["out"], POINTER(wintypes.DWORD), "pdwState")),
]

IMMDeviceCollection._methods_ = [
    COMMETHOD([], HRESULT, "GetCount", (["out"], POINTER(wintypes.UINT), "pcDevices")),
    COMMETHOD([], HRESULT, "Item", (["in"], wintypes.UINT, "nDevice"), (["out"], POINTER(POINTER(IMMDevice)), "ppDevice")),
]

IMMNotificationClient._methods_ = [
    COMMETHOD([], HRESULT, "OnDeviceStateChanged", (["in"], wintypes.LPCWSTR, "pwstrDeviceId"), (["in"], wintypes.DWORD, "dwNewState")),
    COMMETHOD([], HRESULT, "OnDeviceAdded", (["in"], wintypes.LPCWSTR, "pwstrDeviceId")),
    COMMETHOD([], HRESULT, "OnDeviceRemoved", (["in"], wintypes.LPCWSTR, "pwstrDeviceId")),
    COMMETHOD([], HRESULT, "OnDefaultDeviceChanged", (["in"], wintypes.DWORD, "flow"), (["in"], wintypes.DWORD, "role"), (["in"], wintypes.LPCWSTR, "pwstrDefaultDeviceId")),
    COMMETHOD([], HRESULT, "OnPropertyValueChanged", (["in"], wintypes.LPCWSTR, "pwstrDeviceId"), (["in"], POINTER(PROPERTYKEY), "key")),
]

IMMDeviceEnumerator._methods_ = [
    COMMETHOD([], HRESULT, "EnumAudioEndpoints", (["in"], wintypes.DWORD, "dataFlow"), (["in"], wintypes.DWORD, "dwStateMask"), (["out"], POINTER(POINTER(IMMDeviceCollection)), "ppDevices")),
    COMMETHOD([], HRESULT, "GetDefaultAudioEndpoint", (["in"], wintypes.DWORD, "dataFlow"), (["in"], wintypes.DWORD, "role"), (["out"], POINTER(POINTER(IMMDevice)), "ppEndpoint")),
    COMMETHOD([], HRESULT, "GetDevice", (["in"], wintypes.LPCWSTR, "pwstrId"), (["out"], POINTER(POINTER(IMMDevice)), "ppDevice")),
    COMMETHOD([], HRESULT, "RegisterEndpointNotificationCallback", (["in"], POINTER(IMMNotificationClient), "pClient")),
    COMMETHOD([], HRESULT, "UnregisterEndpointNotificationCallback", (["in"], POINTER(IMMNotificationClient), "pClient")),
]

IPolicyConfig._methods_ = [
    COMMETHOD([], HRESULT, "GetMixFormat", (["in"], wintypes.LPCWSTR, "wszDeviceId"), (["out"], POINTER(c_void_p), "ppFormat")),
    COMMETHOD([], HRESULT, "GetDeviceFormat", (["in"], wintypes.LPCWSTR, "wszDeviceId"), (["in"], wintypes.INT, "bDefault"), (["out"], POINTER(c_void_p), "ppFormat")),
    COMMETHOD([], HRESULT, "ResetDeviceFormat", (["in"], wintypes.LPCWSTR, "wszDeviceId")),
    COMMETHOD([], HRESULT, "SetDeviceFormat", (["in"], wintypes.LPCWSTR, "wszDeviceId"), (["in"], c_void_p, "endpointFormat"), (["in"], c_void_p, "mixFormat")),
    COMMETHOD([], HRESULT, "GetProcessingPeriod", (["in"], wintypes.LPCWSTR, "wszDeviceId"), (["in"], wintypes.INT, "bDefault"), (["out"], POINTER(c_void_p), "pmftDefaultPeriod"), (["out"], POINTER(c_void_p), "pmftMinimumPeriod")),
    COMMETHOD([], HRESULT, "SetProcessingPeriod", (["in"], wintypes.LPCWSTR, "wszDeviceId"), (["in"], POINTER(c_void_p), "pmftPeriod")),
    COMMETHOD([], HRESULT, "GetShareMode", (["in"], wintypes.LPCWSTR, "wszDeviceId"), (["out"], POINTER(c_void_p), "pMode")),
    COMMETHOD([], HRESULT, "SetShareMode", (["in"], wintypes.LPCWSTR, "wszDeviceId"), (["in"], POINTER(c_void_p), "pMode")),
    COMMETHOD([], HRESULT, "GetPropertyValue", (["in"], wintypes.LPCWSTR, "wszDeviceId"), (["in"], POINTER(PROPERTYKEY), "key"), (["out"], POINTER(PROPVARIANT), "pv")),
    COMMETHOD([], HRESULT, "SetPropertyValue", (["in"], wintypes.LPCWSTR, "wszDeviceId"), (["in"], POINTER(PROPERTYKEY), "key"), (["in"], POINTER(PROPVARIANT), "pv")),
    COMMETHOD([], HRESULT, "SetDefaultEndpoint", (["in"], wintypes.LPCWSTR, "wszDeviceId"), (["in"], wintypes.DWORD, "role")),
    COMMETHOD([], HRESULT, "SetEndpointVisibility", (["in"], wintypes.LPCWSTR, "wszDeviceId"), (["in"], wintypes.INT, "bVisible")),
]

PKEY_DEVICE_FRIENDLY_NAME = PROPERTYKEY(
    GUID("{A45C254E-DF1C-4EFD-8020-67D146A850E0}"), 14
)

ole32.PropVariantClear.argtypes = [POINTER(PROPVARIANT)]
ole32.PropVariantClear.restype = HRESULT


@dataclass(frozen=True)
class AudioDeviceInfo:
    id: str
    name: str


class DefaultOutputNotificationClient(COMObject):
    _com_interfaces_ = [IMMNotificationClient]

    def __init__(self, callback: Callable[[str], None]) -> None:
        super().__init__()
        self._callback = callback

    def OnDeviceStateChanged(self, this, pwstrDeviceId, dwNewState) -> int:
        return 0

    def OnDeviceAdded(self, this, pwstrDeviceId) -> int:
        return 0

    def OnDeviceRemoved(self, this, pwstrDeviceId) -> int:
        return 0

    def OnDefaultDeviceChanged(
        self, this, flow, role, pwstrDefaultDeviceId
    ) -> int:
        if flow == ERENDER and role == ROLE_CONSOLE:
            try:
                self._callback(pwstrDefaultDeviceId or "")
            except Exception:
                LOGGER.exception("Default output change callback failed")
        return 0

    def OnPropertyValueChanged(self, this, pwstrDeviceId, key) -> int:
        return 0


class AudioController:
    def __init__(self) -> None:
        self._com_initialized = False
        self._notification_client: Optional[DefaultOutputNotificationClient] = None
        self._co_initialize()
        self._enumerator = self._create_device_enumerator()
        self._policy = self._create_policy_config()

    def close(self) -> None:
        self.unregister_default_output_listener()
        if self._com_initialized:
            comtypes.CoUninitialize()
            self._com_initialized = False

    def register_default_output_listener(
        self, callback: Callable[[str], None]
    ) -> None:
        self.unregister_default_output_listener()
        client = DefaultOutputNotificationClient(callback)
        self._enumerator.RegisterEndpointNotificationCallback(client)
        self._notification_client = client

    def unregister_default_output_listener(self) -> None:
        if not self._notification_client:
            return
        try:
            self._enumerator.UnregisterEndpointNotificationCallback(
                self._notification_client
            )
        finally:
            self._notification_client = None

    def list_render_devices(self) -> List[AudioDeviceInfo]:
        collection = self._enumerator.EnumAudioEndpoints(
            ERENDER,
            DEVICE_STATE_ACTIVE,
        )

        count = collection.GetCount()

        devices: List[AudioDeviceInfo] = []
        for index in range(count):
            device = collection.Item(index)
            devices.append(
                AudioDeviceInfo(
                    id=self._get_device_id(device),
                    name=self._get_device_name(device),
                )
            )

        devices.sort(key=lambda item: (item.name.lower(), item.id.lower()))
        return devices

    def get_default_output_device_id(self, role: int = ROLE_CONSOLE) -> Optional[str]:
        device = self._enumerator.GetDefaultAudioEndpoint(ERENDER, role)
        return self._get_device_id(device)

    def get_device_by_id(self, device_id: str) -> Optional[AudioDeviceInfo]:
        if not device_id:
            return None

        try:
            device = self._enumerator.GetDevice(device_id)
            return AudioDeviceInfo(id=device_id, name=self._get_device_name(device))
        except Exception:
            LOGGER.warning("Audio device not found: %s", device_id)
            return None

    def set_default_output_device(self, device_id: str) -> None:
        if not device_id:
            raise ValueError("device_id is required")
        for role in (ROLE_CONSOLE, ROLE_MULTIMEDIA, ROLE_COMMUNICATIONS):
            self._policy.SetDefaultEndpoint(device_id, role)

    def _co_initialize(self) -> None:
        if self._com_initialized:
            return
        comtypes.CoInitialize()
        self._com_initialized = True

    @staticmethod
    def _create_device_enumerator() -> POINTER(IMMDeviceEnumerator):
        return comtypes.CoCreateInstance(
            GUID("{BCDE0395-E52F-467C-8E3D-C4579291692E}"),
            interface=IMMDeviceEnumerator,
            clsctx=CLSCTX_ALL,
        )

    @staticmethod
    def _create_policy_config() -> POINTER(IPolicyConfig):
        return comtypes.CoCreateInstance(
            GUID("{870AF99C-171D-4F9E-AF0D-E63DF40C2BC9}"),
            interface=IPolicyConfig,
            clsctx=CLSCTX_ALL,
        )

    def _get_device_name(self, device: POINTER(IMMDevice)) -> str:
        store = device.OpenPropertyStore(STGM_READ)
        prop = store.GetValue(PKEY_DEVICE_FRIENDLY_NAME)
        try:
            if prop.vt == VT_LPWSTR and prop.data.pwszVal:
                return prop.data.pwszVal
            return "未命名设备"
        finally:
            ole32.PropVariantClear(byref(prop))

    @staticmethod
    def _get_device_id(device: POINTER(IMMDevice)) -> str:
        raw = device.GetId()
        if isinstance(raw, str):
            return raw
        return raw.value or ""
