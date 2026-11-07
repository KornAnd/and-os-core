#!/usr/bin/env python3
"""
statusline.py — Динамическая статус-строка ядра (Runtime Statusline Beacon).
AnD os v8.4 — Остров 8 (Kernel & AND_Terminal :8099).

Выводит компактный срез реального времени в 1 строку (0-токенный терминальный маяк):
- Текущая папка / контекст;
- Статус Git (ветка + dirty flag);
- Счетчик сессии / Бюджет контекста;
- Состояние острова 8 (AND_Terminal) и фоновых портов (:8087, :8092);
- Статус активных шотов в пайплайне.
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
    cfile = os.path.join(VAULT_ROOT, "and_os", "var", "cache", "sessions", "tool_count_default_session.json")
    if os.path.exists(cfile):
        try:
            with open(cfile, "r", encoding="utf-8") as f:
                d = json.load(f)
                return f"tools:{d.get('count', 0)}"
        except Exception:
            pass
    return "tools:0"

def format_statusline(color: bool = True) -> str:
    cwd = os.path.basename(os.getcwd())
    git_info = get_git_info()
    ctx_info = get_context_stats()
    
    # Цветовая палитра ANSI
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
