import logging

import requests
import urllib3
from requests.auth import HTTPDigestAuth

from philips_ctl.config import PhilipsConfig
from philips_ctl.exceptions import PhilipsConnectionError, PhilipsAuthError

urllib3.disable_warnings()

log = logging.getLogger(__name__)


class PhilipsClient:

    def __init__(self, config: PhilipsConfig):
        self.config = config
        self.base_url = f"https://{config.host}:1926"
        self.session = requests.Session()
        self.session.verify = False
        self.session.timeout = config.timeout
        if config.has_creds:
            self.session.auth = HTTPDigestAuth(config.username, config.password)

    def get(self, path):
        url = f"{self.base_url}/{path}"
        log.debug("GET %s", url)
        try:
            r = self.session.get(url)
        except requests.ConnectionError as e:
            raise PhilipsConnectionError(f"Cannot reach {self.config.host}: {e}") from e
        except requests.Timeout as e:
            raise PhilipsConnectionError(f"Timeout connecting to {self.config.host}") from e

        log.debug("Response: %d %s", r.status_code, r.text[:200] if r.text else "")

        if r.status_code == 401:
            raise PhilipsAuthError("Authentication failed. Re-run: philips-ctl bruteforce")
        if r.status_code == 200 and r.text.strip():
            return r.json()
        return None

    def post(self, path, data):
        url = f"{self.base_url}/{path}"
        log.debug("POST %s %s", url, data)
        try:
            r = self.session.post(url, json=data)
        except requests.ConnectionError as e:
            raise PhilipsConnectionError(f"Cannot reach {self.config.host}: {e}") from e
        except requests.Timeout as e:
            raise PhilipsConnectionError(f"Timeout connecting to {self.config.host}") from e

        log.debug("Response: %d %s", r.status_code, r.text[:200] if r.text else "")

        if r.status_code == 401:
            raise PhilipsAuthError("Authentication failed. Re-run: philips-ctl bruteforce")
        if r.status_code == 200 and r.text.strip():
            return r.json()
        return r.status_code

    def post_unauthenticated(self, path, data):
        url = f"{self.base_url}/{path}"
        log.debug("POST (no auth) %s", url)
        try:
            r = requests.post(url, json=data, verify=False, timeout=self.config.timeout)
        except requests.ConnectionError as e:
            raise PhilipsConnectionError(f"Cannot reach {self.config.host}: {e}") from e
        return r
