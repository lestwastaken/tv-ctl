from __future__ import annotations

from bravia_ctl.ircc import CODES, build_soap_body, get_code, list_keys


def test_get_code_returns_correct_value():
    assert get_code("mute") == "AAAAAQAAAAEAAAAUAw=="
    assert get_code("home") == "AAAAAQAAAAEAAABgAw=="
    assert get_code("netflix") == "AAAAAgAAABoAAAB8Aw=="


def test_get_code_is_case_insensitive():
    assert get_code("Mute") == get_code("mute")
    assert get_code("VOLUMEUP") == get_code("volumeup")
    assert get_code("Netflix") == get_code("netflix")


def test_get_code_returns_none_for_unknown():
    assert get_code("nonexistent_key") is None
    assert get_code("") is None


def test_list_keys_is_sorted():
    keys = list_keys()
    assert keys == sorted(keys)


def test_list_keys_contains_expected_keys():
    keys = list_keys()
    for expected in ["mute", "volumeup", "volumedown", "home", "back",
                     "confirm", "up", "down", "left", "right",
                     "play", "pause", "stop", "netflix", "youtube",
                     "hdmi1", "hdmi2", "poweroff", "wakeup"]:
        assert expected in keys


def test_codes_dict_has_no_empty_values():
    for name, code in CODES.items():
        assert code, f"Empty code for key '{name}'"
        assert code.endswith("=="), f"Key '{name}' code doesn't look like base64: {code}"


def test_partner_apps_are_present():
    for i in range(1, 21):
        assert f"partnerapp{i}" in CODES


def test_build_soap_body_contains_code():
    body = build_soap_body("AAAAAQAAAAEAAAAUAw==")
    assert "AAAAAQAAAAEAAAAUAw==" in body
    assert "X_SendIRCC" in body
    assert "IRCCCode" in body
    assert '<?xml version="1.0"?>' in body


def test_build_soap_body_is_valid_xml():
    import xml.etree.ElementTree as ET
    body = build_soap_body("AAAAAQAAAAEAAAAUAw==")
    ET.fromstring(body)


def test_aliases_share_same_code():
    assert get_code("back") == get_code("return")
    assert get_code("sleep") == get_code("poweroff")
    assert get_code("guide") == get_code("epg")
    assert get_code("display") == get_code("info")
