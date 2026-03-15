from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

from bravia_ctl import __version__
from bravia_ctl.client import BraviaClient
from bravia_ctl.config import load_config
from bravia_ctl.exceptions import BraviaAuthError, BraviaConnectionError, BraviaError
from bravia_ctl.ircc import get_code, list_keys

logger = logging.getLogger(__name__)


def _print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def _result_or_raw(data: dict) -> Any:
    if "result" in data:
        return data["result"]
    return data



def cmd_power(client: BraviaClient, args: argparse.Namespace) -> None:
    from bravia_ctl.commands import get_power_status, set_power
    if args.action == "on":
        _print_json(_result_or_raw(set_power(client, on=True)))
    elif args.action == "off":
        _print_json(_result_or_raw(set_power(client, on=False)))
    else:
        _print_json(_result_or_raw(get_power_status(client)))
        print("\nUsage: bravia-ctl power [on|off]")


def cmd_volume(client: BraviaClient, args: argparse.Namespace) -> None:
    from bravia_ctl.commands import get_volume, set_volume, set_mute
    if args.action == "set" and args.level is not None:
        _print_json(_result_or_raw(set_volume(client, args.level)))
    elif args.action == "mute":
        _print_json(_result_or_raw(set_mute(client, muted=True)))
    elif args.action == "unmute":
        _print_json(_result_or_raw(set_mute(client, muted=False)))
    else:
        _print_json(_result_or_raw(get_volume(client)))
        print("\nUsage: bravia-ctl volume [set N|mute|unmute]")


def cmd_input(client: BraviaClient, args: argparse.Namespace) -> None:
    from bravia_ctl.commands import get_inputs, set_input
    if args.action == "set" and args.uri:
        _print_json(_result_or_raw(set_input(client, args.uri)))
    else:
        _print_json(_result_or_raw(get_inputs(client)))
        print("\nUsage: bravia-ctl input [set URI]")


def cmd_app(client: BraviaClient, args: argparse.Namespace) -> None:
    from bravia_ctl.commands import get_apps, launch_app, get_app_status
    if args.action == "launch" and args.uri:
        _print_json(_result_or_raw(launch_app(client, args.uri)))
    elif args.action == "status":
        _print_json(_result_or_raw(get_app_status(client)))
    else:
        apps = get_apps(client)
        for app in apps:
            print(f"  {app.get('title', '?'):30s}  {app.get('uri', '')}")
        print("\nUsage: bravia-ctl app [launch URI|status]")


def cmd_key(client: BraviaClient, args: argparse.Namespace) -> None:
    if args.list_keys:
        keys = list_keys()
        for i in range(0, len(keys), 5):
            print("  " + ", ".join(keys[i:i + 5]))
        return

    name = args.name
    if not name:
        print("Usage: bravia-ctl key <name>", file=sys.stderr)
        print("", file=sys.stderr)
        print("Available keys:", file=sys.stderr)
        keys = list_keys()
        for i in range(0, len(keys), 5):
            print("  " + ", ".join(keys[i:i + 5]), file=sys.stderr)
        sys.exit(1)

    code = get_code(name)
    if not code:
        print(f"Unknown key '{name}'. Available keys:", file=sys.stderr)
        keys = list_keys()
        for i in range(0, len(keys), 5):
            print("  " + ", ".join(keys[i:i + 5]), file=sys.stderr)
        sys.exit(1)

    ok = client.send_ircc(code)
    print(f"{'OK' if ok else 'FAILED'}: {name}")


def cmd_ircc(client: BraviaClient, args: argparse.Namespace) -> None:
    ok = client.send_ircc(args.code)
    print(f"{'OK' if ok else 'FAILED'}")


def cmd_info(client: BraviaClient, _args: argparse.Namespace) -> None:
    from bravia_ctl.commands import get_system_info
    _print_json(_result_or_raw(get_system_info(client)))


def cmd_time(client: BraviaClient, _args: argparse.Namespace) -> None:
    from bravia_ctl.commands import get_current_time
    _print_json(_result_or_raw(get_current_time(client)))


def cmd_interface(client: BraviaClient, _args: argparse.Namespace) -> None:
    from bravia_ctl.commands import get_interface_info
    _print_json(_result_or_raw(get_interface_info(client)))


def cmd_network(client: BraviaClient, _args: argparse.Namespace) -> None:
    from bravia_ctl.commands import get_network_settings
    _print_json(_result_or_raw(get_network_settings(client)))


def cmd_remote_codes(client: BraviaClient, _args: argparse.Namespace) -> None:
    from bravia_ctl.commands import get_remote_codes
    codes = get_remote_codes(client)
    for c in codes:
        print(f"  {c['name']:25s}  {c['value']}")


def cmd_schemes(client: BraviaClient, _args: argparse.Namespace) -> None:
    from bravia_ctl.commands import get_schemes
    _print_json(_result_or_raw(get_schemes(client)))


def cmd_sources(client: BraviaClient, args: argparse.Namespace) -> None:
    from bravia_ctl.commands import get_sources
    _print_json(_result_or_raw(get_sources(client, args.scheme)))


def cmd_content(client: BraviaClient, args: argparse.Namespace) -> None:
    from bravia_ctl.commands import get_content_list
    _print_json(_result_or_raw(get_content_list(client, args.uri)))


def cmd_playing(client: BraviaClient, _args: argparse.Namespace) -> None:
    from bravia_ctl.commands import get_playing
    _print_json(_result_or_raw(get_playing(client)))


def cmd_speaker(client: BraviaClient, _args: argparse.Namespace) -> None:
    from bravia_ctl.commands import get_speaker_settings
    _print_json(_result_or_raw(get_speaker_settings(client)))


def cmd_supported(client: BraviaClient, _args: argparse.Namespace) -> None:
    from bravia_ctl.commands import get_supported_functions
    _print_json(_result_or_raw(get_supported_functions(client)))


def cmd_apps_status(client: BraviaClient, _args: argparse.Namespace) -> None:
    from bravia_ctl.commands import get_app_status
    _print_json(_result_or_raw(get_app_status(client)))


def cmd_publickey(client: BraviaClient, _args: argparse.Namespace) -> None:
    from bravia_ctl.commands import get_public_key
    _print_json(_result_or_raw(get_public_key(client)))


def cmd_screen(client: BraviaClient, _args: argparse.Namespace) -> None:
    from bravia_ctl.commands import get_screen_settings
    _print_json(get_screen_settings(client))


def cmd_screenshot(client: BraviaClient, args: argparse.Namespace) -> None:
    from bravia_ctl.commands import get_screenshot
    data = get_screenshot(client)
    if data:
        out = args.output or "screenshot.png"
        Path(out).write_bytes(data)
        print(f"Saved to {out} ({len(data)} bytes)")
    else:
        print("No screenshot data returned.", file=sys.stderr)
        sys.exit(1)


def cmd_reboot(client: BraviaClient, _args: argparse.Namespace) -> None:
    from bravia_ctl.commands import reboot
    _print_json(_result_or_raw(reboot(client)))


def cmd_browser(client: BraviaClient, args: argparse.Namespace) -> None:
    from bravia_ctl.commands import get_browser_url, open_url
    if args.action == "open" and args.url:
        _print_json(_result_or_raw(open_url(client, args.url)))
    else:
        _print_json(_result_or_raw(get_browser_url(client)))
        print("\nUsage: bravia-ctl browser [open URL]")


def cmd_textform(client: BraviaClient, args: argparse.Namespace) -> None:
    from bravia_ctl.commands import get_text_form, set_text_form
    if args.text:
        _print_json(_result_or_raw(set_text_form(client, args.text)))
    else:
        _print_json(_result_or_raw(get_text_form(client)))
        print("\nUsage: bravia-ctl textform [TEXT]")


def cmd_powersaving(client: BraviaClient, _args: argparse.Namespace) -> None:
    from bravia_ctl.commands import get_power_saving
    _print_json(_result_or_raw(get_power_saving(client)))


def cmd_wol(client: BraviaClient, _args: argparse.Namespace) -> None:
    from bravia_ctl.commands import get_wol_mode
    _print_json(_result_or_raw(get_wol_mode(client)))



def cmd_auth(client: BraviaClient, args: argparse.Namespace) -> None:
    from bravia_ctl import auth

    if args.action == "pair":
        cookie = auth.pair_with_pin(client)
        if not cookie:
            sys.exit(1)
    elif args.action == "bruteforce-psk":
        psk = auth.bruteforce_psk(client)
        if psk:
            print(f"Found PSK: {psk}")
        else:
            print("No working PSK found.", file=sys.stderr)
            sys.exit(1)
    elif args.action == "bruteforce-pin":
        cookie = auth.bruteforce_pin(client, delay=args.delay)
        if not cookie:
            sys.exit(1)
    elif args.action == "test":
        _cmd_auth_test(client)
    else:
        _cmd_auth_test(client)


def _cmd_auth_test(client: BraviaClient) -> None:
    from bravia_ctl.discovery import auth_boundary_test
    results = auth_boundary_test(client)
    for r in results:
        status = r["status"]
        color = "+" if status == "OK" else "!" if status == "FORBIDDEN" else "?"
        print(f"  [{color}] {status:12s}  {r['service']}/{r['method']}")



def cmd_probe(client: BraviaClient, _args: argparse.Namespace) -> None:
    from bravia_ctl.discovery import probe_services
    results = probe_services(client)
    for svc, methods in results.items():
        print(f"\n  [{svc}] ({len(methods)} methods)")
        for m in methods:
            print(f"    {m}")


def cmd_apis(client: BraviaClient, _args: argparse.Namespace) -> None:
    from bravia_ctl.discovery import get_supported_apis
    data = get_supported_apis(client)
    if "result" in data:
        for svc in data["result"][0]:
            print(f"\n  [{svc.get('service', '?')}]")
            for m in svc.get("apis", []):
                versions = ",".join(m.get("versions", []))
                print(f"    {m.get('name', '?')} (v{versions})")
    else:
        _print_json(data)



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bravia-ctl",
        description="Control Sony Bravia Android TVs via the REST API.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--host", help="TV IP address or hostname")
    parser.add_argument("--psk", help="Pre-Shared Key for authentication")
    parser.add_argument("--timeout", type=int, help="HTTP timeout in seconds")
    parser.add_argument("--config", help="Path to .env file")
    parser.add_argument("--cookie", help="Path to auth cookie file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug output")
    parser.add_argument("--json", action="store_true", help="Force JSON output")

    sub = parser.add_subparsers(dest="command", help="Available commands")

    p = sub.add_parser("power", help="Power control")
    p.add_argument("action", nargs="?", default="status", choices=["status", "on", "off"])

    p = sub.add_parser("volume", help="Volume control")
    p.add_argument("action", nargs="?", default="get", choices=["get", "set", "mute", "unmute"])
    p.add_argument("level", nargs="?", type=int, help="Volume level (0-100)")

    p = sub.add_parser("input", help="Input/HDMI control")
    p.add_argument("action", nargs="?", default="list", choices=["list", "set"])
    p.add_argument("uri", nargs="?", help="Input URI (e.g. extInput:hdmi?port=1)")

    p = sub.add_parser("app", help="App control")
    p.add_argument("action", nargs="?", default="list", choices=["list", "launch", "status"])
    p.add_argument("uri", nargs="?", help="App URI")

    p = sub.add_parser("key", help="Simulate a remote button press (e.g. bravia-ctl key mute)")
    p.add_argument("name", nargs="?", help="Key to send: home, mute, volumeup, netflix, hdmi1, etc.")
    p.add_argument("-l", "--list", dest="list_keys", action="store_true", help="Show all available key names")

    p = sub.add_parser("ircc", help="Send raw IRCC base64 code")
    p.add_argument("code", help="Base64-encoded IRCC code")

    sub.add_parser("info", help="System info (model, serial, MAC)")
    sub.add_parser("time", help="TV clock")
    sub.add_parser("interface", help="Interface/firmware info")
    sub.add_parser("network", help="Network settings")
    sub.add_parser("remote-codes", help="Dump all IRCC codes from TV")
    sub.add_parser("schemes", help="Content URI schemes")
    sub.add_parser("playing", help="Currently playing content")
    sub.add_parser("speaker", help="Speaker settings")
    sub.add_parser("supported", help="Supported system functions")
    sub.add_parser("publickey", help="Encryption public key")
    sub.add_parser("screen", help="Screen/video settings")
    sub.add_parser("powersaving", help="Power saving mode")
    sub.add_parser("wol", help="Wake-on-LAN mode")
    sub.add_parser("reboot", help="Reboot the TV")

    p = sub.add_parser("sources", help="Content sources")
    p.add_argument("scheme", nargs="?", help="Scheme to filter (e.g. tv, extInput)")

    p = sub.add_parser("content", help="Browse content list")
    p.add_argument("uri", help="Source URI")

    p = sub.add_parser("screenshot", help="Grab screenshot from TV")
    p.add_argument("-o", "--output", help="Output file path (default: screenshot.png)")

    p = sub.add_parser("browser", help="Browser control")
    p.add_argument("action", nargs="?", default="get", choices=["get", "open"])
    p.add_argument("url", nargs="?", help="URL to open")

    p = sub.add_parser("textform", help="Get/set text input on TV")
    p.add_argument("text", nargs="?", help="Text to type")

    p = sub.add_parser("auth", help="Authentication")
    p.add_argument(
        "action", choices=["pair", "bruteforce-psk", "bruteforce-pin", "test"],
        help="Auth action",
    )
    p.add_argument("--delay", type=float, default=0.02, help="Delay between PIN attempts (seconds)")

    sub.add_parser("probe", help="Enumerate API services and methods")
    sub.add_parser("apis", help="List all supported API methods")

    return parser



COMMAND_MAP = {
    "power": cmd_power,
    "volume": cmd_volume,
    "input": cmd_input,
    "app": cmd_app,
    "key": cmd_key,
    "ircc": cmd_ircc,
    "info": cmd_info,
    "time": cmd_time,
    "interface": cmd_interface,
    "network": cmd_network,
    "remote-codes": cmd_remote_codes,
    "schemes": cmd_schemes,
    "sources": cmd_sources,
    "content": cmd_content,
    "playing": cmd_playing,
    "speaker": cmd_speaker,
    "supported": cmd_supported,
    "publickey": cmd_publickey,
    "screen": cmd_screen,
    "screenshot": cmd_screenshot,
    "reboot": cmd_reboot,
    "browser": cmd_browser,
    "textform": cmd_textform,
    "powersaving": cmd_powersaving,
    "wol": cmd_wol,
    "auth": cmd_auth,
    "probe": cmd_probe,
    "apis": cmd_apis,
}


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        sys.exit(0)

    level = logging.WARNING
    if args.verbose:
        level = logging.INFO
    if args.debug:
        level = logging.DEBUG
    logging.basicConfig(
        level=level,
        format="  [%(levelname)s] %(message)s",
    )

    config = load_config(
        host=args.host,
        psk=args.psk,
        timeout=args.timeout,
        cookie_path=args.cookie,
        debug=args.debug,
        config_file=args.config,
    )

    if args.command == "key" and getattr(args, "list_keys", False):
        keys = list_keys()
        for i in range(0, len(keys), 5):
            print("  " + ", ".join(keys[i:i + 5]))
        return

    try:
        config.validate()
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    client = BraviaClient(config)

    try:
        handler = COMMAND_MAP[args.command]
        handler(client, args)
    except BraviaAuthError as exc:
        print(f"Auth error: {exc}", file=sys.stderr)
        print("Run 'bravia-ctl auth pair' or 'bravia-ctl auth bruteforce-pin' to authenticate.",
              file=sys.stderr)
        sys.exit(1)
    except BraviaConnectionError as exc:
        print(f"Connection error: {exc}", file=sys.stderr)
        sys.exit(1)
    except BraviaError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
    finally:
        client.close()


if __name__ == "__main__":
    main()
