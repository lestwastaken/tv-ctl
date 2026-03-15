from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_ENV_FILE = Path.cwd() / ".env"
DEFAULT_COOKIE_FILE = Path.home() / ".config" / "bravia-ctl" / "cookie"


@dataclass
class BraviaConfig:
    host: str = ""
    psk: str | None = None
    timeout: int = 5
    cookie_path: Path = field(default_factory=lambda: DEFAULT_COOKIE_FILE)
    debug: bool = False

    def validate(self) -> None:
        if not self.host:
            raise ValueError(
                "No TV host specified. Use --host, BRAVIA_HOST env var, "
                "or set BRAVIA_HOST in .env"
            )


def _load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("\"'")
        values[key] = value
    return values


def load_config(
    *,
    host: str | None = None,
    psk: str | None = None,
    timeout: int | None = None,
    cookie_path: str | None = None,
    debug: bool = False,
    config_file: str | None = None,
) -> BraviaConfig:
    env_path = Path(config_file) if config_file else DEFAULT_ENV_FILE
    env_cfg = _load_env_file(env_path)

    def get(cli_val: str | None, env_key: str) -> str | None:
        return cli_val or os.environ.get(env_key) or env_cfg.get(env_key)

    resolved_timeout_str = get(str(timeout) if timeout else None, "BRAVIA_TIMEOUT")
    resolved_timeout = int(resolved_timeout_str) if resolved_timeout_str else 5

    return BraviaConfig(
        host=get(host, "BRAVIA_HOST") or "",
        psk=get(psk, "BRAVIA_PSK"),
        timeout=resolved_timeout,
        cookie_path=Path(
            get(cookie_path, "BRAVIA_COOKIE_PATH") or str(DEFAULT_COOKIE_FILE)
        ),
        debug=debug,
    )
