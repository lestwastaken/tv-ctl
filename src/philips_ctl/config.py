import os
import sys
import json
from dataclasses import dataclass
from pathlib import Path


def _get_config_dir():
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "philips-ctl"


CREDS_PATH = _get_config_dir() / "credentials.json"


@dataclass
class PhilipsConfig:
    host: str = ""
    username: str = ""
    password: str = ""
    timeout: int = 5

    def validate(self):
        if not self.host:
            raise ValueError("No host configured. Set PHILIPS_HOST or pass as argument.")

    @property
    def has_creds(self):
        return bool(self.username and self.password)


def _load_env_file(path=None):
    env_path = Path(path) if path else Path(".env")
    if not env_path.exists():
        return {}
    result = {}
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            result[k.strip()] = v.strip().strip("'\"")
    return result


def load_config(*, host=None, timeout=None):
    env = _load_env_file()
    creds = load_credentials()

    if not host:
        host = os.environ.get("PHILIPS_HOST") or env.get("PHILIPS_HOST") or ""
    if not host and creds:
        host = creds.get("host", "")

    username = os.environ.get("PHILIPS_USER") or env.get("PHILIPS_USER") or ""
    password = os.environ.get("PHILIPS_PASS") or env.get("PHILIPS_PASS") or ""

    if not username and creds:
        username = creds.get("username", "")
        password = creds.get("password", "")

    return PhilipsConfig(
        host=host,
        username=username,
        password=password,
        timeout=timeout or int(os.environ.get("PHILIPS_TIMEOUT") or env.get("PHILIPS_TIMEOUT", "5")),
    )


def load_credentials():
    if CREDS_PATH.exists():
        return json.loads(CREDS_PATH.read_text())
    return None


def save_credentials(host, username, password):
    CREDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    CREDS_PATH.write_text(json.dumps({
        "host": host,
        "username": username,
        "password": password,
    }, indent=2))
    print(f"[+] Credentials saved to {CREDS_PATH}")
