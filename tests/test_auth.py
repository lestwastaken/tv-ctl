from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from bravia_ctl.auth import COMMON_PSKS, bruteforce_psk
from bravia_ctl.client import BraviaClient
from bravia_ctl.config import BraviaConfig


@pytest.fixture
def config(tmp_path):
    return BraviaConfig(
        host="192.168.1.100",
        psk="0000",
        timeout=3,
        cookie_path=tmp_path / "cookie",
    )


@pytest.fixture
def client(config):
    return BraviaClient(config)


def test_common_psks_list_is_not_empty():
    assert len(COMMON_PSKS) > 0


def test_common_psks_contains_defaults():
    assert "0000" in COMMON_PSKS
    assert "1234" in COMMON_PSKS
    assert "sony" in COMMON_PSKS


def test_bruteforce_psk_finds_match(client):
    def mock_post(url, headers, json, timeout):
        resp = MagicMock()
        if headers.get("X-Auth-PSK") == "1234":
            resp.status_code = 200
            resp.json.return_value = {"result": [{"status": "active"}], "id": 1}
        else:
            resp.status_code = 403
        return resp

    with patch("bravia_ctl.auth.requests.post", side_effect=mock_post):
        result = bruteforce_psk(client)
        assert result == "1234"


def test_bruteforce_psk_returns_none_when_no_match(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 403

    with patch("bravia_ctl.auth.requests.post", return_value=mock_resp):
        result = bruteforce_psk(client)
        assert result is None


def test_bruteforce_psk_handles_connection_errors(client):
    import requests
    with patch("bravia_ctl.auth.requests.post", side_effect=requests.exceptions.ConnectionError):
        result = bruteforce_psk(client)
        assert result is None
