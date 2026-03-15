from __future__ import annotations

import base64
from typing import Any

from bravia_ctl.client import BraviaClient


def get_system_info(client: BraviaClient) -> dict[str, Any]:
    return client.json_rpc("system", "getSystemInformation")


def get_power_status(client: BraviaClient) -> dict[str, Any]:
    return client.json_rpc("system", "getPowerStatus")


def set_power(client: BraviaClient, *, on: bool) -> dict[str, Any]:
    return client.json_rpc("system", "setPowerStatus", [{"status": on}])


def reboot(client: BraviaClient) -> dict[str, Any]:
    return client.json_rpc("system", "requestReboot")


def get_current_time(client: BraviaClient) -> dict[str, Any]:
    return client.json_rpc("system", "getCurrentTime")


def get_interface_info(client: BraviaClient) -> dict[str, Any]:
    return client.json_rpc("system", "getInterfaceInformation")


def get_device_mode(client: BraviaClient) -> dict[str, Any]:
    return client.json_rpc("system", "getDeviceMode")


def get_power_saving(client: BraviaClient) -> dict[str, Any]:
    return client.json_rpc("system", "getPowerSavingMode")


def get_wol_mode(client: BraviaClient) -> dict[str, Any]:
    return client.json_rpc("system", "getWolMode")


def get_supported_functions(client: BraviaClient) -> dict[str, Any]:
    return client.json_rpc("system", "getSystemSupportedFunction")


def get_storage(client: BraviaClient) -> dict[str, Any]:
    return client.json_rpc("system", "getStorageList")


def get_network_settings(client: BraviaClient) -> dict[str, Any]:
    return client.json_rpc("system", "getNetworkSettings", [{"netif": ""}])


def get_remote_codes(client: BraviaClient) -> list[dict[str, str]]:
    data = client.json_rpc("system", "getRemoteControllerInfo")
    if "result" in data and len(data["result"]) > 1:
        return data["result"][1]
    return []


def get_led_status(client: BraviaClient) -> dict[str, Any]:
    return client.json_rpc("system", "getLEDIndicatorStatus")


def get_remote_device_settings(client: BraviaClient) -> dict[str, Any]:
    return client.json_rpc("system", "getRemoteDeviceSettings", [{"target": ""}])


def get_screenshot(client: BraviaClient) -> bytes | None:
    data = client.json_rpc("system", "getScreenshot")
    if "result" in data:
        for item in data["result"]:
            if isinstance(item, dict) and "data" in item:
                return base64.b64decode(item["data"])
    return None


def get_volume(client: BraviaClient) -> dict[str, Any]:
    return client.json_rpc("audio", "getVolumeInformation")


def set_volume(client: BraviaClient, level: int) -> dict[str, Any]:
    return client.json_rpc(
        "audio", "setAudioVolume",
        [{"target": "speaker", "volume": str(level)}],
        version="1.2",
    )


def set_mute(client: BraviaClient, *, muted: bool) -> dict[str, Any]:
    return client.json_rpc("audio", "setAudioMute", [{"status": muted}])


def get_speaker_settings(client: BraviaClient) -> dict[str, Any]:
    return client.json_rpc("audio", "getSpeakerSettings", [{"target": ""}])


def get_sound_settings(client: BraviaClient) -> dict[str, Any]:
    return client.json_rpc("audio", "getSoundSettings", [{"target": ""}])


def get_inputs(client: BraviaClient) -> dict[str, Any]:
    return client.json_rpc("avContent", "getCurrentExternalInputsStatus")


def set_input(client: BraviaClient, uri: str) -> dict[str, Any]:
    return client.json_rpc("avContent", "setPlayContent", [{"uri": uri}])


def get_playing(client: BraviaClient) -> dict[str, Any]:
    return client.json_rpc("avContent", "getPlayingContentInfo")


def get_schemes(client: BraviaClient) -> dict[str, Any]:
    return client.json_rpc("avContent", "getSchemeList")


def get_sources(client: BraviaClient, scheme: str | None = None) -> dict[str, Any]:
    params = [{"scheme": scheme}] if scheme else []
    return client.json_rpc("avContent", "getSourceList", params)


def get_content_list(client: BraviaClient, source: str) -> dict[str, Any]:
    return client.json_rpc(
        "avContent", "getContentList",
        [{"uri": source, "stIdx": 0, "cnt": 50}],
    )


def get_favorites(client: BraviaClient) -> dict[str, Any]:
    return client.json_rpc("avContent", "getFavoriteList")


def get_parental_settings(client: BraviaClient) -> dict[str, Any]:
    return client.json_rpc("avContent", "getParentalRatingSettings")


def get_apps(client: BraviaClient) -> list[dict[str, str]]:
    data = client.json_rpc("appControl", "getApplicationList")
    if "result" in data:
        return data["result"][0]
    return []


def launch_app(client: BraviaClient, uri: str) -> dict[str, Any]:
    return client.json_rpc("appControl", "setActiveApp", [{"uri": uri}])


def get_app_status(client: BraviaClient) -> dict[str, Any]:
    return client.json_rpc("appControl", "getApplicationStatusList")


def get_text_form(client: BraviaClient) -> dict[str, Any]:
    return client.json_rpc("appControl", "getTextForm")


def set_text_form(client: BraviaClient, text: str) -> dict[str, Any]:
    return client.json_rpc("appControl", "setTextForm", [{"text": text}])


def get_browser_url(client: BraviaClient) -> dict[str, Any]:
    return client.json_rpc("browser", "getTextUrl")


def set_browser_url(client: BraviaClient, url: str) -> dict[str, Any]:
    return client.json_rpc("browser", "setTextUrl", [{"url": url}])


def open_url(client: BraviaClient, url: str) -> dict[str, Any]:
    return client.json_rpc("browser", "actBrowserControl", [{"control": "openUrl", "url": url}])


def get_public_key(client: BraviaClient) -> dict[str, Any]:
    return client.json_rpc("encryption", "getPublicKey")


SCREEN_METHODS = [
    "getMultiScreenMode", "getBannerMode", "getSceneSetting",
    "getPipSubScreenPosition", "getAudioSourceScreen",
]


def get_screen_settings(client: BraviaClient) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for method in SCREEN_METHODS:
        try:
            data = client.json_rpc("videoScreen", method)
            results[method] = data.get("result", data.get("error"))
        except Exception as exc:
            results[method] = str(exc)
    return results


def get_cec_settings(client: BraviaClient) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for method in ["setCecControlMode", "setMhlAutoInputChangeMode",
                    "setMhlPowerFeedMode", "setPowerSyncMode"]:
        try:
            data = client.json_rpc("cec", method)
            results[method] = data
        except Exception as exc:
            results[method] = str(exc)
    return results
