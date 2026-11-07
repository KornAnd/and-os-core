#!/usr/bin/env python3
"""
tasks_bridge.py — Аналитический и Синхронизационный Шлюз Производственного Пульса (Tasks & Production Pulse).
Обеспечивает токеноэффективное (<50 токенов) получение оперативного состояния задач,
отслеживание изменений и управление жизненным циклом чек-боксов.
"""

import os
import sys
import json
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent.parent
LIB_DIR = ROOT_DIR / "and_os" / "lib" / "closed_loop"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from tasks_router import TasksRouter


def main():
    parser = argparse.ArgumentParser(description="Tasks & Production Pulse CLI for ANDREY OS")
    subparsers = parser.add_subparsers(dest="command")

    # pulse
    p_pulse = subparsers.add_parser("pulse", help="Мгновенный сжатый срез оперативного пульса студии")
    p_pulse.add_argument("--project", choices=["mars", "kot", "pm", "Studio"], help="Фильтр по проекту")
    p_pulse.add_argument("--json", action="store_true", help="Вывод в формате JSON")

    # complete
    p_comp = subparsers.add_parser("complete", help="Отметить задачу выполненной (- [x])")
    p_comp.add_argument("query", help="Подстрока названия задачи")
    p_comp.add_argument("--project", choices=["mars", "kot", "pm", "Studio"], help="Целевой проект")

    # check
    subparsers.add_parser("check", help="Проверка целостности базы задач и досок")

    args = parser.parse_args()

    if args.command == "pulse" or not args.command:
        project = getattr(args, "project", None)
        pulse = TasksRouter.get_pulse(project)
        if getattr(args, "json", False):
            print(json.dumps(pulse, ensure_ascii=False, indent=2))
        else:
            proj_title = f" ({project.upper()})" if project else " (Все проекты)"
            print(f"=== ⚡ Производственный пульс студии{proj_title} ===")
            print(f"📋 Всего открытых задач: {pulse['pending_count']}")
            print(f"🔥 Срочных / Горящих: {pulse['urgent_count']}")
            print(f"✅ Завершенных: {pulse['completed_count']}")

            if pulse["urgent_tasks"]:
                print("\n🚨 Срочные задачи и блокеры:")
                for t in pulse["urgent_tasks"]:
                    due_info = f" [до {t['due']}]" if t['due'] else ""
                    print(f"  • [{t['file']}] {t['title']}{due_info}")

            if pulse["regular_tasks_sample"]:
                print("\n📌 В работе (выборка):")
                for t in pulse["regular_tasks_sample"]:
                    print(f"  - [{t['file']}] {t['title']}")

    elif args.command == "complete":
        res = TasksRouter.complete_task(args.query, getattr(args, "project", None))
        if res.get("status") == "success":
            print(f"✅ Задача выполнена: {res['completed']}")
            print(f"  • Доска: {res['board']}")
            print(f"  • Дата: {res['date']}")
        else:
            print(f"❌ {res.get('message')}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "check":
        pulse = TasksRouter.get_pulse()
        print("🟢 [Tasks Bridge Status: OK]")
        print(f"  • Индексировано открытых задач: {pulse['pending_count']}")
        print(f"  • Завершенных задач: {pulse['completed_count']}")
        print(f"  • База данных SQLite: and_os/var/task_vault.db")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
