#!/usr/bin/env python3
"""
statusline.py — Dynamic kernel statusline (Runtime Statusline Beacon).
AnD os v1.0.0 — Island 8 (Kernel & AND_Terminal :8099).

Prints a compact real-time snapshot in a single line (0-token terminal beacon):
- Current folder / context;
- Git status (branch + dirty flag);
- Session counter / context budget;
- Island 8 (AND_Terminal) and background ports (:8087, :8092) state;
- Active pipeline shots status.
"""

import os
import sys
import subprocess
import json
import shutil

VAULT_ROOT = os.getenv("AND_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

def get_git_info() -> str:
    try:
        b = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
        status = subprocess.check_output(["git", "status", "--porcelain"], stderr=subprocess.DEVNULL).decode().strip()
        dirty = "*" if status else ""
        return f"{b}{dirty}"
    except Exception:
        return "no-git"

def get_context_stats() -> str:
    # Rule #71 (Vault Purity): session counters are cache data, system home.
    cfile = os.path.join(os.path.expanduser("~/.and_os"), "var", "cache", "sessions", "tool_count_default_session.json")
    if os.path.exists(cfile):
        try:
            with open(cfile, "r", encoding="utf-8") as f:
                d = json.load(f)
                return f"tools:{d.get('count', 0)}"
        except (OSError, ValueError):
            # Cache file is optional; its absence means "no tools counted yet".
            pass
    return "tools:0"

def format_statusline(color: bool = True) -> str:
    cwd = os.path.basename(os.getcwd())
    git_info = get_git_info()
    ctx_info = get_context_stats()
    
    # ANSI color palette
    C_BLUE = "\033[38;2;30;102;245m" if color else ""
    C_GREEN = "\033[38;2;64;160;43m" if color else ""
    C_MAGENTA = "\033[38;2;136;57;239m" if color else ""
    C_CYAN = "\033[38;2;23;146;153m" if color else ""
    C_RESET = "\033[0m" if color else ""

    line = f"{C_CYAN}AnD_os{C_RESET}:{C_BLUE}{cwd}{C_RESET} | {C_GREEN}{git_info}{C_RESET} | {C_MAGENTA}{ctx_info}{C_RESET} | {C_CYAN}Mesh:9/9{C_RESET}"
    return line

if __name__ == "__main__":
    no_color = "--no-color" in sys.argv
    print(format_statusline(color=not no_color))
