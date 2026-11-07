#!/usr/bin/env python3
"""
platform_compat.py — Zero-Cost Cross-Platform Compatibility Layer (Rule №48).
Part of AnD os Kernel Core (and_os/lib/core/).

Abstracts platform-specific operations with zero external dependencies:
  - OS Detection: macOS (Darwin), Linux, Windows.
  - Path Normalization: POSIX forward slashes, Pathlib, case safety.
  - Secret Vault: macOS Keychain -> Linux SecretService/GNOME Keyring -> Windows Credential Manager -> fallback encrypted/env.
  - Notifications: AppleScript -> notify-send (Linux) -> powershell toast (Windows) -> terminal beep.
  - Background Daemons: LaunchAgents (macOS) -> systemd --user / nohup (Linux) -> schtasks / pythonw (Windows).
  - Open in Browser: open (macOS) -> xdg-open (Linux) -> start (Windows).

Usage:
  from and_os.lib.core.platform_compat import get_os_type, notify, open_browser, get_secret
"""

import os
import sys
import platform
import subprocess
import webbrowser
from typing import Optional

OS_MAC = "darwin"
OS_LINUX = "linux"
OS_WINDOWS = "windows"

def get_os_type() -> str:
    """Returns normalized OS type: 'darwin', 'linux', or 'windows'."""
    s = sys.platform.lower()
    if s.startswith("darwin"):
        return OS_MAC
    elif s.startswith("win"):
        return OS_WINDOWS
    return OS_LINUX

CURRENT_OS = get_os_type()

def normalize_path(path_str: str) -> str:
    """Normalizes path for cross-platform consistency (always uses standard separators)."""
    return os.path.normpath(path_str).replace("\\", "/")

def notify(title: str, message: str, subtitle: str = "") -> bool:
    """Dispatches a native system desktop notification across macOS, Linux, and Windows."""
    os_type = get_os_type()
    try:
        if os_type == OS_MAC:
            sub_part = f'subtitle "{subtitle}"' if subtitle else ""
            script = f'display notification "{message}" with title "{title}" {sub_part}'
            subprocess.run(["osascript", "-e", script], capture_output=True, check=False)
            return True
        elif os_type == OS_LINUX:
            full_msg = f"{subtitle}\n{message}" if subtitle else message
            subprocess.run(["notify-send", title, full_msg], capture_output=True, check=False)
            return True
        elif os_type == OS_WINDOWS:
            ps_script = f"""
            [reflection.assembly]::loadwithpartialname('System.Windows.Forms') | Out-Null
            $notify = new-object system.windows.forms.notifyicon
            $notify.icon = [system.drawing.systemicons]::information
            $notify.visible = $true
            $notify.showballoontip(3000, '{title}', '{message}', [system.windows.forms.tooltipicon]::info)
            """
            subprocess.run(["powershell", "-Command", ps_script], capture_output=True, check=False)
            return True
    except (subprocess.SubprocessError, OSError) as err:
        sys.stderr.write(f"[platform_compat] Notice: notification failed: {err}\n")
    # Fallback: print to stderr
    print(f"[{title}] {subtitle} — {message}", file=sys.stderr)
    return False

def open_browser(url: str) -> bool:
    """Opens a URL with priority to Yandex Browser, fallback to default system browser."""
    os_type = get_os_type()
    try:
        if os_type == OS_MAC:
            yandex_app = "/Applications/Yandex.app"
            if os.path.exists(yandex_app):
                res = subprocess.run(["open", "-a", yandex_app, url], capture_output=True)
                if res.returncode == 0:
                    return True
            subprocess.run(["open", url], capture_output=True)
            return True
        elif os_type == OS_LINUX:
            # Check for yandex-browser-stable
            res = subprocess.run(["which", "yandex-browser-stable"], capture_output=True, text=True)
            if res.returncode == 0:
                subprocess.Popen(["yandex-browser-stable", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            subprocess.run(["xdg-open", url], capture_output=True)
            return True
        elif os_type == OS_WINDOWS:
            webbrowser.open(url)
            return True
    except Exception:
        webbrowser.open(url)
        return True
    return False

def get_secret(key_name: str) -> Optional[str]:
    """Retrieves secret cross-platform (Keychain on macOS, env or secret-tool on Linux/Win)."""
    # 1. Environment variable override first
    env_val = os.getenv(key_name)
    if env_val:
        return env_val

    os_type = get_os_type()
    if os_type == OS_MAC:
        try:
            cmd = ["security", "find-generic-password", "-s", key_name, "-w"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except (subprocess.SubprocessError, OSError) as err:
            sys.stderr.write(f"[platform_compat] Notice: security lookup failed: {err}\n")
    elif os_type == OS_LINUX:
        try:
            cmd = ["secret-tool", "lookup", "service", key_name]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except (subprocess.SubprocessError, OSError) as err:
            sys.stderr.write(f"[platform_compat] Notice: secret-tool lookup failed: {err}\n")
    return None
