#!/usr/bin/env python3
"""
telemetry_logger.py — Модуль быстрых логов телеметрии (IPC Bus).
Модульная программа для добавления валидированных записей в and_os/lib/skills/telemetry.md
без загрузки всего файла в контекст LLM.

Использование:
  python3 telemetry_logger.py --task "Название задачи" --mode WORK --skill "sys.audit" --ctx min --result success
"""

import os
import sys
from pathlib import Path
_vroot = str(Path(__file__).resolve().parents[2])
if _vroot not in sys.path:
    sys.path.insert(0, _vroot)
from and_os.lib.core.vault_safe_io import vault_safe_write

import sys
import json
import argparse
from datetime import datetime

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
TELEMETRY_PATH = os.path.join(VAULT_ROOT, "and_os/lib/skills/telemetry.md")

def log_telemetry(task, mode, skill, ctx, result):
    if not os.path.exists(TELEMETRY_PATH):
        print(f"Ошибка: {TELEMETRY_PATH} не найден.")
        sys.exit(1)

    today_str = datetime.now().strftime("%Y-%m-%d")
    entry_line = f"- {today_str} | {mode} | {skill} | {task} | {result} | {ctx} | 1 | 0 | new | + | -\n"

    with open(TELEMETRY_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if "[[CONTEXT|← Наверх]]" in content:
        parts = content.rsplit("[[CONTEXT|← Наверх]]", 1)
        new_content = parts[0] + entry_line + "\n[[CONTEXT|← Наверх]]" + parts[1]
        with open(TELEMETRY_PATH, "w", encoding="utf-8") as f:
            f.write(new_content)
    else:
        with open(TELEMETRY_PATH, "a", encoding="utf-8") as f:
            f.write(entry_line)

    now_str = datetime.now().isoformat()
    res = {
        "status": "SUCCESS",
        "logged_entry": entry_line.strip(),
        "timestamp": now_str
    }
    print(json.dumps(res, ensure_ascii=False, indent=2))

def main():
    parser = argparse.ArgumentParser(description="Telemetry Logger Module")
    parser.add_argument("--task", type=str, required=True, help="Название выполненной задачи")
    parser.add_argument("--mode", type=str, choices=["QUICK", "WORK", "STRATEGIC", "SYSTEM"], default="WORK", help="Режим работы")
    parser.add_argument("--skill", type=str, required=True, help="Использованный скилл/модуль")
    parser.add_argument("--ctx", type=str, choices=["min", "work", "full", "compressed"], default="min", help="Уровень контекста")
    parser.add_argument("--result", type=str, default="success", help="Результат задачи")
    
    args = parser.parse_args()
    log_telemetry(args.task, args.mode, args.skill, args.ctx, args.result)

if __name__ == "__main__":
    main()
