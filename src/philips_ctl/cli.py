from __future__ import annotations

import argparse
import json
import logging
import sys
import time

from philips_ctl import __version__
from philips_ctl.client import PhilipsClient
from philips_ctl.config import load_config, save_credentials
from philips_ctl.commands import KEYS
from philips_ctl.exceptions import PhilipsAuthError, PhilipsConnectionError, PhilipsError

log = logging.getLogger(__name__)


def _print_json(data) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_power(client: PhilipsClient, args: argparse.Namespace) -> None:
    from philips_ctl.commands import get_power, set_power, standby, get_ambilight
    if args.action == "on":
        set_power(client, "On")
        print("[+] Powering on")
    elif args.action == "off":
        standby(client)
        print("[+] Standby sent")
    else:
        r = get_power(client)
        if r and r.get("powerstate"):
            print(f"Power: {r['powerstate']}")
        else:
            amb = get_ambilight(client)
            power = amb.get("power")
            if power and power.get("power"):
                print(f"Power: {power['power'].title()}")
            else:
                print("Power: unknown (endpoint not supported on this model)")
        print("\nUsage: philips-ctl power [on|off]")


def cmd_volume(client: PhilipsClient, args: argparse.Namespace) -> None:
    from philips_ctl.commands import get_volume, set_volume, toggle_mute
    if args.action == "set" and args.level is not None:
        set_volume(client, args.level)
        print(f"[+] Volume set to {args.level}")
    elif args.action == "mute":
        result = toggle_mute(client)
        if result is not None:
            print(f"[+] {'Muted' if result else 'Unmuted'}")
    else:
        r = get_volume(client)
        if r:
            muted = " (muted)" if r.get("muted") else ""
            print(f"Volume: {r['current']}/{r['max']}{muted}")
        print("\nUsage: philips-ctl volume [set N|mute]")


def cmd_key(client: PhilipsClient, args: argparse.Namespace) -> None:
    from philips_ctl.commands import send_key
    if args.list_keys:
        for k in KEYS:
            print(f"  {k}")
        return
    if not args.name:
        print("Usage: philips-ctl key <name> [--count N]")
        print("Use 'philips-ctl key --list' to see available keys")
        return
    for i in range(args.count):
        send_key(client, args.name)
        if args.count > 1 and i < args.count - 1:
            time.sleep(0.1)
    print(f"[+] Sent {args.name}" + (f" x{args.count}" if args.count > 1 else ""))


def cmd_system(client: PhilipsClient, args: argparse.Namespace) -> None:
    from philips_ctl.commands import get_system
    r = get_system(client)
    if r:
        _print_json(r)


def cmd_ambilight(client: PhilipsClient, args: argparse.Namespace) -> None:
    from philips_ctl.commands import get_ambilight, set_ambilight_mode
    if args.action == "set" and args.mode:
        set_ambilight_mode(client, args.mode)
        print(f"[+] Ambilight set to {args.mode}")
    else:
        r = get_ambilight(client)
        for k, v in r.items():
            if v:
                print(f"{k.title()}: {json.dumps(v)}")
        print("\nUsage: philips-ctl ambilight [set internal|manual|expert|off]")


def cmd_channels(client: PhilipsClient, args: argparse.Namespace) -> None:
    from philips_ctl.commands import get_channels
    r = get_channels(client)
    if r:
        for ch in r.get("Channel", [])[:30]:
            print(f"  {ch.get('preset', '?'):>4s}  {ch.get('name', 'unknown')}")


def cmd_apps(client: PhilipsClient, args: argparse.Namespace) -> None:
    from philips_ctl.commands import get_applications
    r = get_applications(client)
    if r:
        for app in r.get("applications", []):
            label = app.get("label", "?")
            pkg = app.get("intent", {}).get("component", {}).get("packageName", "")
            print(f"  {label:30s}  {pkg}")


def cmd_launch(client: PhilipsClient, args: argparse.Namespace) -> None:
    from philips_ctl.commands import launch_app
    label = launch_app(client, args.app)
    if label:
        print(f"[+] Launching {label}")
    else:
        print(f"[-] App '{args.app}' not found")


def cmd_sources(client: PhilipsClient, args: argparse.Namespace) -> None:
    from philips_ctl.commands import get_sources
    r = get_sources(client)
    if r:
        _print_json(r)


def cmd_playing(client: PhilipsClient, args: argparse.Namespace) -> None:
    from philips_ctl.commands import get_current_activity
    r = get_current_activity(client)
    if r:
        _print_json(r)


def cmd_network(client: PhilipsClient, args: argparse.Namespace) -> None:
    from philips_ctl.commands import get_network
    r = get_network(client)
    if r:
        _print_json(r)


def cmd_auth(client: PhilipsClient, args: argparse.Namespace) -> None:
    from philips_ctl.auth import pair_with_pin, bruteforce_pin
    from philips_ctl.commands import get_volume

    host = client.config.host

    if args.action == "pair":
        pin = input("Enter PIN shown on TV: ")
        creds, err = pair_with_pin(host, pin)
        if err:
            print(f"[-] {err}")
            return
        save_credentials(creds["host"], creds["username"], creds["password"])
        print("[+] Paired!")

    elif args.action == "bruteforce":
        creds = bruteforce_pin(host, workers=args.workers)
        if creds:
            save_credentials(creds["host"], creds["username"], creds["password"])
            new_config = load_config(host=host)
            new_client = PhilipsClient(new_config)
            vol = get_volume(new_client)
            if vol:
                print(f"[+] Verified: volume is {vol['current']}/{vol['max']}")
            else:
                print("[!] Creds saved but verification failed")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="philips-ctl",
        description="Pentest tool for Philips Android TVs with JointSpace API",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--host", help="TV IP address or hostname")
    parser.add_argument("--timeout", type=int, help="Request timeout in seconds")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug output")

    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("auth", help="Authentication (pair / bruteforce)")
    p.add_argument("action", choices=["pair", "bruteforce"], help="Auth action")
    p.add_argument("--workers", type=int, default=50, help="Parallel workers for bruteforce")

    p = sub.add_parser("power", help="Power control")
    p.add_argument("action", nargs="?", default="get", choices=["get", "on", "off"])

    p = sub.add_parser("volume", help="Volume control")
    p.add_argument("action", nargs="?", default="get", choices=["get", "set", "mute"])
    p.add_argument("level", nargs="?", type=int, help="Volume level (0-60)")

    p = sub.add_parser("key", help="Send remote key (e.g. philips-ctl key VolumeUp)")
    p.add_argument("name", nargs="?", help="Key name")
    p.add_argument("-l", "--list", dest="list_keys", action="store_true", help="List all keys")
    p.add_argument("-c", "--count", type=int, default=1, help="Send key N times")

    sub.add_parser("system", help="System info (model, firmware, country)")
    sub.add_parser("channels", help="Channel list")
    sub.add_parser("apps", help="Installed applications")
    sub.add_parser("sources", help="Input sources")
    sub.add_parser("playing", help="Current activity")
    sub.add_parser("network", help="Network devices")

    p = sub.add_parser("launch", help="Launch app by name")
    p.add_argument("app", help="App name or package name")

    p = sub.add_parser("ambilight", help="Ambilight control")
    p.add_argument("action", nargs="?", default="get", choices=["get", "set"])
    p.add_argument("mode", nargs="?", help="Mode: internal, manual, expert, off")

    return parser


COMMAND_MAP = {
    "power": cmd_power,
    "volume": cmd_volume,
    "key": cmd_key,
    "system": cmd_system,
    "ambilight": cmd_ambilight,
    "channels": cmd_channels,
    "apps": cmd_apps,
    "launch": cmd_launch,
    "sources": cmd_sources,
    "playing": cmd_playing,
    "network": cmd_network,
    "auth": cmd_auth,
}


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        sys.exit(0)

    level = logging.WARNING
    if getattr(args, "verbose", False):
        level = logging.INFO
    if getattr(args, "debug", False):
        level = logging.DEBUG
    logging.basicConfig(level=level, format="  [%(levelname)s] %(message)s")

    if args.command == "key" and getattr(args, "list_keys", False):
        for k in KEYS:
            print(f"  {k}")
        return

    config = load_config(host=getattr(args, "host", None))

    try:
        config.validate()
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    client = PhilipsClient(config)

    try:
        handler = COMMAND_MAP[args.command]
        handler(client, args)
    except PhilipsAuthError as exc:
        print(f"Auth error: {exc}", file=sys.stderr)
        print("Run 'philips-ctl auth bruteforce' to authenticate.", file=sys.stderr)
        sys.exit(1)
    except PhilipsConnectionError as exc:
        print(f"Connection error: {exc}", file=sys.stderr)
        sys.exit(1)
    except PhilipsError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
