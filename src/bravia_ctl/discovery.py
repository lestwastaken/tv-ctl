from __future__ import annotations

import logging
from typing import Any

import requests

from bravia_ctl.client import BraviaClient
from bravia_ctl.exceptions import BraviaAuthError, BraviaConnectionError

logger = logging.getLogger(__name__)

ALL_SERVICES = [
    "system", "avContent", "audio", "appControl", "videoScreen",
    "guide", "encryption", "accessControl", "cec", "recording",
    "browser", "notification",
]

AUTH_TEST_METHODS: list[tuple[str, str] | tuple[str, str, list]] = [
    ("system", "getCurrentTime"),
    ("system", "getDeviceMode"),
    ("system", "getInterfaceInformation"),
    ("system", "getLEDIndicatorStatus"),
    ("system", "getNetworkSettings", [{"netif": ""}]),
    ("system", "getPowerSavingMode"),
    ("system", "getPowerStatus"),
    ("system", "getRemoteControllerInfo"),
    ("system", "getRemoteDeviceSettings", [{"target": ""}]),
    ("system", "getScreenshot"),
    ("system", "getSystemInformation"),
    ("system", "getSystemSupportedFunction"),
    ("system", "getWolMode"),
    ("system", "getStorageList"),
    ("avContent", "getCurrentExternalInputsStatus"),
    ("avContent", "getPlayingContentInfo"),
    ("avContent", "getSchemeList"),
    ("avContent", "getSourceList"),
    ("avContent", "getFavoriteList"),
    ("avContent", "getParentalRatingSettings"),
    ("audio", "getVolumeInformation"),
    ("audio", "getSpeakerSettings", [{"target": ""}]),
    ("audio", "getSoundSettings", [{"target": ""}]),
    ("appControl", "getApplicationList"),
    ("appControl", "getApplicationStatusList"),
    ("appControl", "getWebAppStatus"),
    ("appControl", "getTextForm"),
    ("videoScreen", "getMultiScreenMode"),
    ("videoScreen", "getBannerMode"),
    ("videoScreen", "getSceneSetting"),
    ("videoScreen", "getPipSubScreenPosition"),
    ("videoScreen", "getAudioSourceScreen"),
    ("encryption", "getPublicKey"),
    ("browser", "getTextUrl"),
    ("cec", "setCecControlMode"),
]


def probe_services(client: BraviaClient) -> dict[str, list[str]]:
    results: dict[str, list[str]] = {}

    for svc in ALL_SERVICES:
        url = f"{client.base_url}/sony/{svc}"
        try:
            resp = requests.post(
                url,
                headers={"Content-Type": "application/json",
                         **({"X-Auth-PSK": client.config.psk} if client.config.psk else {})},
                cookies=client._get_cookies(),
                json={"method": "getMethodTypes", "id": 1, "params": [""], "version": "1.0"},
                timeout=3,
            )
        except Exception as exc:
            logger.debug("%s: %s", svc, exc)
            continue

        if resp.status_code == 403:
            continue

        try:
            data = resp.json()
        except Exception:
            continue

        methods_raw = data.get("results") or data.get("result", [])
        method_names = []
        for m in methods_raw:
            if isinstance(m, list) and m:
                method_names.append(m[0])
            elif isinstance(m, str):
                method_names.append(m)

        if method_names:
            results[svc] = method_names

    return results


def auth_boundary_test(client: BraviaClient) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []

    for entry in AUTH_TEST_METHODS:
        svc, method = entry[0], entry[1]
        params = entry[2] if len(entry) > 2 else []

        try:
            data = client.json_rpc(svc, method, params)
            status = "OK" if "result" in data else f"ERR:{data.get('error', '?')}"
        except BraviaAuthError:
            status = "FORBIDDEN"
        except BraviaConnectionError as exc:
            status = f"CONN_ERR:{exc}"
        except Exception as exc:
            status = f"ERR:{exc}"

        results.append({"service": svc, "method": method, "status": status})

    return results


def get_supported_apis(client: BraviaClient) -> dict[str, Any]:
    return client.json_rpc("guide", "getSupportedApiInfo", [{"services": ALL_SERVICES}])
