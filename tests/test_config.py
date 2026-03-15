from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from bravia_ctl.config import BraviaConfig, load_config


def test_default_config_has_no_host():
    with patch.dict(os.environ, {}, clear=True):
        config = load_config(config_file="/nonexistent/.env")
        assert config.host == ""
        assert config.psk is None
        assert config.timeout == 5


def test_validate_raises_without_host():
    config = BraviaConfig(host="")
    with pytest.raises(ValueError, match="No TV host specified"):
        config.validate()


def test_validate_passes_with_host():
    config = BraviaConfig(host="192.168.1.1")
    config.validate()


def test_cli_args_override_env():
    with patch.dict(os.environ, {"BRAVIA_HOST": "env-host", "BRAVIA_PSK": "env-psk"}):
        config = load_config(host="cli-host", psk="cli-psk")
        assert config.host == "cli-host"
        assert config.psk == "cli-psk"


def test_env_vars_are_used():
    with patch.dict(os.environ, {"BRAVIA_HOST": "10.0.0.1", "BRAVIA_PSK": "1234"}, clear=True):
        config = load_config(config_file="/nonexistent/.env")
        assert config.host == "10.0.0.1"
        assert config.psk == "1234"


def test_env_file_loading(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("BRAVIA_HOST=file-host\nBRAVIA_PSK=file-psk\nBRAVIA_TIMEOUT=10\n")

    with patch.dict(os.environ, {}, clear=True):
        config = load_config(config_file=str(env_file))
        assert config.host == "file-host"
        assert config.psk == "file-psk"
        assert config.timeout == 10


def test_env_file_handles_quotes(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text('BRAVIA_HOST="quoted-host"\nBRAVIA_PSK=\'quoted-psk\'\n')

    with patch.dict(os.environ, {}, clear=True):
        config = load_config(config_file=str(env_file))
        assert config.host == "quoted-host"
        assert config.psk == "quoted-psk"


def test_env_file_skips_comments(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("# this is a comment\nBRAVIA_HOST=test-host\n\n# another comment\n")

    with patch.dict(os.environ, {}, clear=True):
        config = load_config(config_file=str(env_file))
        assert config.host == "test-host"


def test_cli_overrides_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("BRAVIA_HOST=file-host\nBRAVIA_PSK=file-psk\n")

    config = load_config(host="cli-host", config_file=str(env_file))
    assert config.host == "cli-host"
    assert config.psk == "file-psk"


def test_missing_env_file_is_fine():
    config = load_config(host="test", config_file="/nonexistent/.env")
    assert config.host == "test"


def test_cookie_path_from_args():
    config = load_config(host="test", cookie_path="/tmp/test-cookie")
    assert config.cookie_path == Path("/tmp/test-cookie")


def test_debug_flag():
    config = load_config(host="test", debug=True)
    assert config.debug is True
