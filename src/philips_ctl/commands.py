KEYS = [
    "Standby", "Back", "Find", "RedColour", "GreenColour", "YellowColour",
    "BlueColour", "Home", "VolumeUp", "VolumeDown", "Mute", "Options",
    "Dot", "Digit0", "Digit1", "Digit2", "Digit3", "Digit4", "Digit5",
    "Digit6", "Digit7", "Digit8", "Digit9", "Info", "CursorUp",
    "CursorDown", "CursorLeft", "CursorRight", "Confirm", "Next",
    "Previous", "Adjust", "WatchTV", "ViewMode", "Teletext", "Subtitle",
    "ChannelStepUp", "ChannelStepDown", "Source", "AmbilightOnOff",
    "PlayPause", "Pause", "FastForward", "Stop", "Rewind", "Record",
    "Online", "Play",
]


def get_system(client):
    return client.get("6/system")


def get_volume(client):
    return client.get("6/audio/volume")


def set_volume(client, level):
    return client.post("6/audio/volume", {"current": level, "muted": False})


def toggle_mute(client):
    vol = get_volume(client)
    if vol:
        new_mute = not vol.get("muted", False)
        client.post("6/audio/volume", {"current": vol["current"], "muted": new_mute})
        return new_mute
    return None


def get_power(client):
    return client.get("6/powerstate")


def set_power(client, state):
    return client.post("6/powerstate", {"powerstate": state})


def send_key(client, key):
    return client.post("6/input/key", {"key": key})


def standby(client):
    return send_key(client, "Standby")


def get_ambilight(client):
    mode = client.get("6/ambilight/mode")
    power = client.get("6/ambilight/power")
    topology = client.get("6/ambilight/topology")
    return {"mode": mode, "power": power, "topology": topology}


def set_ambilight_mode(client, mode):
    return client.post("6/ambilight/mode", {"current": mode})


def get_channels(client):
    return client.get("6/channeldb/tv/channelLists/all")


def get_applications(client):
    return client.get("6/applications")


def launch_app(client, target):
    apps = get_applications(client)
    if not apps:
        return None
    for app in apps.get("applications", []):
        label = app.get("label", "").lower()
        pkg = app.get("intent", {}).get("component", {}).get("packageName", "").lower()
        if target.lower() in label or target.lower() in pkg:
            intent = app.get("intent", {})
            result = client.post("6/activities/launch", intent)
            if result is None or (isinstance(result, int) and result != 200):
                client.post("6/applications/launch", intent)
            return app.get("label")
    return None


def get_sources(client):
    return client.get("6/sources")


def get_current_activity(client):
    return client.get("6/activities/current")


def get_network(client):
    return client.get("6/network/devices")
