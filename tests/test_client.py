from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bravia_ctl.client import BraviaClient
from bravia_ctl.config import BraviaConfig
from bravia_ctl.exceptions import BraviaAuthError, BraviaConnectionError


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


def test_base_url(client):
    assert client.base_url == "http://192.168.1.100"


def test_psk_header_is_set(client):
    assert client._session.headers["X-Auth-PSK"] == "0000"


def test_no_psk_header_when_none(tmp_path):
    config = BraviaConfig(host="10.0.0.1", cookie_path=tmp_path / "cookie")
    c = BraviaClient(config)
    assert "X-Auth-PSK" not in c._session.headers


def test_cookies_empty_without_file(client):
    assert client._get_cookies() == {}


def test_cookies_loaded_from_file(tmp_path):
    cookie_path = tmp_path / "cookie"
    cookie_path.write_text("abc123")
    config = BraviaConfig(host="10.0.0.1", cookie_path=cookie_path)
    c = BraviaClient(config)
    assert c._get_cookies() == {"auth": "abc123"}


def test_save_cookie(client, tmp_path):
    client.save_cookie("test_cookie_value")
    assert client._cookie == "test_cookie_value"
    assert client.config.cookie_path.read_text() == "test_cookie_value"
    assert client._get_cookies() == {"auth": "test_cookie_value"}


def test_json_rpc_success(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"result": [{"status": "active"}], "id": 1}

    with patch.object(client._session, "post", return_value=mock_resp):
        result = client.json_rpc("system", "getPowerStatus")
        assert result["result"][0]["status"] == "active"


def test_json_rpc_raises_auth_error_on_403(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"error": [403, "Forbidden"], "id": 1}

    with patch.object(client._session, "post", return_value=mock_resp):
        with pytest.raises(BraviaAuthError, match="forbidden"):
            client.json_rpc("system", "getSystemInformation")


def test_json_rpc_raises_connection_error(client):
    import requests
    with patch.object(client._session, "post", side_effect=requests.exceptions.ConnectionError("refused")):
        with pytest.raises(BraviaConnectionError, match="Cannot reach"):
            client.json_rpc("system", "getPowerStatus")


def test_json_rpc_raises_on_timeout(client):
    import requests
    with patch.object(client._session, "post", side_effect=requests.exceptions.Timeout("timed out")):
        with pytest.raises(BraviaConnectionError, match="timed out"):
            client.json_rpc("system", "getPowerStatus")


def test_send_ircc_success(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200

    with patch.object(client._session, "post", return_value=mock_resp):
        assert client.send_ircc("AAAAAQAAAAEAAAAUAw==") is True


def test_send_ircc_auth_error(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 403

    with patch.object(client._session, "post", return_value=mock_resp):
        with pytest.raises(BraviaAuthError, match="forbidden"):
            client.send_ircc("AAAAAQAAAAEAAAAUAw==")


def test_send_ircc_returns_false_on_non_200(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 500

    with patch.object(client._session, "post", return_value=mock_resp):
        assert client.send_ircc("AAAAAQAAAAEAAAAUAw==") is False
