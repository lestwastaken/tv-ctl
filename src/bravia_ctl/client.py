from __future__ import annotations

import logging
from typing import Any

import requests

from bravia_ctl.config import BraviaConfig
from bravia_ctl.exceptions import BraviaAuthError, BraviaConnectionError
from bravia_ctl.ircc import build_soap_body

logger = logging.getLogger(__name__)


class BraviaClient:
    def __init__(self, config: BraviaConfig) -> None:
        self.config = config
        self._session = requests.Session()
        self._cookie: str | None = self._load_cookie()

        if config.psk:
            self._session.headers["X-Auth-PSK"] = config.psk

    def _load_cookie(self) -> str | None:
        path = self.config.cookie_path
        if path.exists():
            cookie = path.read_text().strip()
            if cookie:
                logger.debug("Loaded auth cookie from %s", path)
                return cookie
        return None

    def save_cookie(self, cookie: str) -> None:
        self.config.cookie_path.parent.mkdir(parents=True, exist_ok=True)
        self.config.cookie_path.write_text(cookie)
        self._cookie = cookie
        logger.info("Auth cookie saved to %s", self.config.cookie_path)

    @property
    def base_url(self) -> str:
        return f"http://{self.config.host}"

    def _get_cookies(self) -> dict[str, str]:
        if self._cookie:
            return {"auth": self._cookie}
        return {}

    def json_rpc(
        self,
        service: str,
        method: str,
        params: list | None = None,
        version: str = "1.0",
    ) -> dict[str, Any]:
        url = f"{self.base_url}/sony/{service}"
        payload = {
            "method": method,
            "id": 1,
            "params": params or [],
            "version": version,
        }

        logger.debug("POST %s  method=%s", url, method)

        try:
            resp = self._session.post(
                url,
                json=payload,
                cookies=self._get_cookies(),
                headers={"Content-Type": "application/json"},
                timeout=self.config.timeout,
            )
        except requests.exceptions.ConnectionError as exc:
            raise BraviaConnectionError(f"Cannot reach {self.config.host}: {exc}") from exc
        except requests.exceptions.Timeout as exc:
            raise BraviaConnectionError(f"Request timed out: {exc}") from exc

        logger.debug("Response %d: %s", resp.status_code, resp.text[:200])

        data = resp.json()

        if "error" in data and isinstance(data["error"], list):
            if data["error"][0] == 403:
                raise BraviaAuthError(
                    f"{service}/{method}: forbidden (auth cookie required)"
                )

        return data

    def send_ircc(self, ircc_code: str) -> bool:
        url = f"{self.base_url}/sony/ircc"
        body = build_soap_body(ircc_code)
        headers = {
            "Content-Type": "text/xml; charset=UTF-8",
            "SOAPACTION": '"urn:schemas-sony-com:service:IRCC:1#X_SendIRCC"',
        }

        logger.debug("IRCC POST %s  code=%s", url, ircc_code)

        try:
            resp = self._session.post(
                url,
                headers=headers,
                data=body,
                cookies=self._get_cookies(),
                timeout=self.config.timeout,
            )
        except requests.exceptions.ConnectionError as exc:
            raise BraviaConnectionError(f"Cannot reach {self.config.host}: {exc}") from exc
        except requests.exceptions.Timeout as exc:
            raise BraviaConnectionError(f"IRCC request timed out: {exc}") from exc

        if resp.status_code == 403:
            raise BraviaAuthError("IRCC command forbidden (auth cookie required)")

        logger.debug("IRCC response: %d", resp.status_code)
        return resp.status_code == 200

    def raw_post(
        self,
        url: str,
        *,
        json: dict | None = None,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> requests.Response:
        try:
            return requests.post(
                url,
                json=json,
                headers=headers,
                timeout=timeout or self.config.timeout,
            )
        except requests.exceptions.ConnectionError as exc:
            raise BraviaConnectionError(f"Cannot reach {self.config.host}: {exc}") from exc
        except requests.exceptions.Timeout as exc:
            raise BraviaConnectionError(f"Request timed out: {exc}") from exc

    def close(self) -> None:
        self._session.close()
