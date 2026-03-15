# tv-ctl

A remote control for Sony Bravia and Philips Android TVs — but with a built-in bruteforce so you never need to manually pair. Both TV brands require a 4-digit PIN to pair new devices, but neither properly defends against brute force. This tool cracks the PIN automatically and gives you full remote control from the command line.

Built by [@lestwastaken](https://github.com/lestwastaken) during OSCP studies after discovering that smart TVs on my home network expose their entire control API to anyone on the LAN.

Includes two tools:

- **`bravia-ctl`** — Sony Bravia Android TVs (JSON-RPC API + IRCC remote)
- **`philips-ctl`** — Philips Android TVs (JointSpace API v6)

## Discovery

While running a full port scan on my home network as part of OSCP exam prep, I found two smart TVs exposing their control APIs to anyone on the LAN with zero authentication required.

### Sony Bravia KD-55X75WL — 17 open TCP ports

```
$ nmap -sV -p- 192.168.2.81

PORT      SERVICE         VERSION
80/tcp    http            nginx
6466/tcp  ssl/unknown     atvremote (Android TV Remote)
6467/tcp  ssl/unknown     atvremote
7000/tcp  rtsp            AirTunes rtspd
8008/tcp  http            Google Cast
8009/tcp  ssl/castv2      Chromecast driver
8443/tcp  ssl/https-alt   Google Cast (SSL)
9000/tcp  ssl/cslistener
9080/tcp  glrpc           NRDP/2025.2.2.0 (Netflix)
33753/tcp upnp            Sony Bravia DLNA
36655/tcp unknown         HTTP 470 "Connection Authorization Required"
45183/tcp unknown         eSDK server
52323/tcp upnp            UPnP DMR (Sony "Huey Sample DMR")
56210/tcp upnp            UPnP MINT-X
...
```

### Philips 32PFS6000/12 — JointSpace API + Google Cast

```
$ nmap -sV -Pn 192.168.2.51

PORT     SERVICE
1925/tcp JointSpace API v6 (HTTP)
1926/tcp JointSpace API v6 (HTTPS)
8008/tcp Google Cast
8009/tcp Google Cast v2 (SSL)
```

**These ports are open by default out of the box.** No user configuration is required — they are enabled the moment the TV connects to a network.

## Security Findings

### Sony Bravia: Bruteforceable 4-Digit Pairing PIN

The Sony Bravia PIN pairing mechanism is vulnerable to brute force:

- The TV uses a **4-digit PIN** (10,000 combinations)
- **The PIN does not change on failure** — same PIN stays valid until dialog timeout
- **No rate limiting** on attempts
- **No lockout** after failed attempts
- The dialog can be **re-triggered programmatically**
- At ~50 attempts/second, full keyspace is exhausted in **~3-4 minutes**

The Pre-Shared Key (PSK) is also bruteforceable — common defaults like `0000` are tried automatically.

### Philips: Hardcoded HMAC Secret Key + PIN Bruteforce

The Philips JointSpace pairing has an even bigger flaw:

- **Every Philips Android TV uses the same hardcoded HMAC secret key** for signing pairing requests
- The PIN is 4 digits (10,000 combinations)
- With the known secret key and 50 parallel workers, the PIN is cracked in **under 3 seconds**
- After pairing, the credentials use HTTP Digest Auth and persist across reboots
- The `/6/system` endpoint leaks device info (model, firmware, country) **without any authentication**

The hardcoded secret key (`ZmVay1EQ...`) is embedded in every Philips Android TV firmware — meaning any Philips TV on your network can be compromised in seconds.

## Supported Models

**Sony Bravia (confirmed):**

- Sony Bravia KD-55X75WL (Android TV, 2023)
- Likely any Sony Bravia Android TV with `/sony/*` REST API

**Philips (confirmed):**

- Philips 32PFS6000/12 (Smart TV, JointSpace v6.1)
- Likely any Philips TV with JointSpace API v6+

Not all endpoints are available on every model. Older Philips TVs (pre-2016) may not support app management. If a command doesn't work on your model, open an issue or PR.

## Prerequisites

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

### Installing uv

**Linux / macOS / WSL:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Homebrew (macOS / Linux):**

```bash
brew install uv
```

**pipx:**

```bash
pipx install uv
```

After installing, restart your terminal and verify:

```bash
uv --version
```

### Installing Python (via uv)

```bash
uv python install 3.12
uv python list
```

## Installation

```bash
git clone https://github.com/lestwastaken/bravia-ctl.git
cd bravia-ctl
uv sync
```

Both `bravia-ctl` and `philips-ctl` are now available:

```bash
uv run bravia-ctl --help
uv run philips-ctl
```

## Quick Start

Both tools follow the same workflow: **bruteforce first, then control**.

### Sony Bravia

```bash
# 1. Set your TV's IP
echo "BRAVIA_HOST=192.168.2.81" > .env

# 2. Bruteforce the PSK (silent, no TV interaction)
bravia-ctl auth bruteforce-psk
echo "BRAVIA_PSK=0000" >> .env

# 3. Bruteforce the pairing PIN for full control (~3-4 min)
bravia-ctl auth bruteforce-pin

# 4. Control the TV
bravia-ctl power
bravia-ctl volume
bravia-ctl key home
```

### Philips

```bash
# 1. Bruteforce the PIN (~3 seconds, saves credentials automatically)
philips-ctl auth bruteforce --host 192.168.2.51

# 2. Control the TV
philips-ctl volume
philips-ctl key VolumeUp
philips-ctl power off
```

## Commands

Both tools share a similar command structure. Not all commands are available on every TV model.

### Authentication

| Command              | bravia-ctl            | philips-ctl      |
| -------------------- | --------------------- | ---------------- |
| Bruteforce PIN       | `auth bruteforce-pin` | `auth bruteforce`|
| Bruteforce PSK       | `auth bruteforce-psk` | —                |
| Manual PIN pair      | `auth pair`           | `auth pair`      |
| Test auth boundaries | `auth test`           | —                |

### Info (read-only)

| Command              | bravia-ctl       | philips-ctl  |
| -------------------- | ---------------- | ------------ |
| System info          | `info`           | `system`     |
| Power state          | `power`          | `power`      |
| Volume               | `volume`         | `volume`     |
| Current activity     | —                | `playing`    |
| Input sources        | `input list`     | `sources`    |
| Ambilight            | —                | `ambilight`  |
| Channel list         | —                | `channels`   |
| Remote key codes     | `remote-codes`   | `key --list` |
| Firmware / interface | `interface`      | `system`     |
| API enumeration      | `probe` / `apis` | —            |
| Speaker config       | `speaker`        | —            |
| TV clock             | `time`           | —            |

### Control (requires pairing)

| Command             | bravia-ctl                      | philips-ctl                |
| ------------------- | ------------------------------- | -------------------------- |
| Power on            | `power on`                      | `power on`                 |
| Power off / standby | `power off`                     | `power off`                |
| Set volume          | `volume set N`                  | `volume set N`             |
| Mute / unmute       | `volume mute` / `volume unmute` | `volume mute` (toggle)     |
| Send remote key     | `key NAME`                      | `key NAME [--count N]`     |
| List remote keys    | `key --list`                    | `key --list`               |
| Switch input        | `input set URI`                 | —                          |
| List apps           | `app list`                      | `apps`                     |
| Launch app          | `app launch URI`                | `launch NAME`              |
| Screenshot          | `screenshot`                    | —                          |
| Open URL            | `browser open URL`              | —                          |
| Type text           | `textform TEXT`                 | —                          |
| Reboot              | `reboot`                        | —                          |
| Network info        | `network`                       | `network`                  |
| Set ambilight       | —                               | `ambilight set MODE`       |

### Remote Keys

**Sony Bravia** — 100+ IRCC keys:

```
back, blue, channeldown, channelup, confirm, down, enter, exit,
forward, green, hdmi1-4, home, input, left, mute, netflix, next,
num0-9, options, pause, play, poweroff, prev, rec, red, return,
rewind, right, stop, subtitle, up, volumedown, volumeup, youtube, ...
```

Use `bravia-ctl key --list` or `bravia-ctl remote-codes` (fetches directly from TV).

**Philips** — JointSpace keys:

```
Standby, Back, Home, VolumeUp, VolumeDown, Mute, CursorUp, CursorDown,
CursorLeft, CursorRight, Confirm, ChannelStepUp, ChannelStepDown,
Source, Play, Pause, PlayPause, Stop, FastForward, Rewind, Record,
Next, Previous, AmbilightOnOff, Info, Options, Subtitle, Teletext, ...
```

Use `philips-ctl key --list` for the full list.

## Configuration

### Sony Bravia

Configuration is resolved in this order (highest wins):

1. **CLI flags**: `--host`, `--psk`, `--timeout`
2. **Environment variables**: `BRAVIA_HOST`, `BRAVIA_PSK`, `BRAVIA_TIMEOUT`
3. **`.env` file** in the current directory

Auth cookie is stored at:

- **Linux**: `~/.config/bravia-ctl/cookie`
- **macOS**: `~/Library/Application Support/bravia-ctl/cookie`
- **Windows**: `%APPDATA%\bravia-ctl\cookie`

### Philips

Configuration is resolved in this order (highest wins):

1. **CLI flags**: `--host`, `--timeout`
2. **Environment variables**: `PHILIPS_HOST`, `PHILIPS_TIMEOUT`
3. **`.env` file** in the current directory

Credentials are saved automatically after `auth bruteforce` or `auth pair`:

- **Linux**: `~/.config/philips-ctl/credentials.json`
- **macOS**: `~/Library/Application Support/philips-ctl/credentials.json`
- **Windows**: `%APPDATA%\philips-ctl\credentials.json`

### .env example

```env
# Sony Bravia
BRAVIA_HOST=192.168.2.81
BRAVIA_PSK=0000

# Philips
PHILIPS_HOST=192.168.2.51
```

## Logging

```bash
# Sony
bravia-ctl -v power     # verbose
bravia-ctl -d power     # debug (full HTTP)

# Philips
philips-ctl -v volume   # verbose
philips-ctl -d volume   # debug (full HTTP)
```

## API Protocols

### Sony — JSON-RPC at `http://<TV_IP>/sony/<service>`

| Service         | Purpose                                                |
| --------------- | ------------------------------------------------------ |
| `system`        | Power, device info, network, remote codes, screenshots |
| `avContent`     | Input switching, content lists, playback               |
| `audio`         | Volume, mute, speaker settings                         |
| `appControl`    | App management, text input                             |
| `videoScreen`   | Picture modes, PIP, multi-screen                       |
| `guide`         | API discovery                                          |
| `encryption`    | Public key retrieval                                   |
| `accessControl` | Device registration (PIN pairing)                      |
| `cec`           | HDMI-CEC control                                       |
| `browser`       | Browser URL control                                    |

### Philips — JointSpace REST at `https://<TV_IP>:1926/6/<endpoint>`

| Endpoint       | Purpose                            |
| -------------- | ---------------------------------- |
| `system`       | Device info, storage               |
| `audio/volume` | Volume control                     |
| `input/key`    | Remote key simulation              |
| `powerstate`   | Power control                      |
| `ambilight/*`  | Ambilight control                  |
| `applications` | App management (newer models only) |
| `channeldb/*`  | Channel database                   |
| `activities/*` | Current activity, app launching    |
| `sources`      | Input sources                      |

## Disclaimer

**This tool is intended for authorized security testing and educational purposes only.**

- Only use it on devices you **own** or have **explicit written permission** to test
- Unauthorized access to computer systems and networks is **illegal** in most jurisdictions
- The author is not responsible for any misuse of this tool

This project was developed as part of personal OSCP exam preparation and home lab research. All testing was performed on the author's own hardware.

## Contributing

If something doesn't work on your TV model, or you want to add support for new features:

- Open a [pull request](https://github.com/lestwastaken/bravia-ctl/pulls)
- File an [issue](https://github.com/lestwastaken/bravia-ctl/issues)
- Reach out to me on GitHub: [@lestwastaken](https://github.com/lestwastaken)

## Author

Built by [@lestwastaken](https://github.com/lestwastaken) while studying for OSCP & OSCP+.

## License

MIT
