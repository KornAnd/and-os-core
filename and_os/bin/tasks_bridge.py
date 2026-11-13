#!/usr/bin/env python3
"""
tasks_bridge.py — Analytical and Synchronization Gateway of the Production Pulse (Tasks & Production Pulse).
Provides token-efficient (<50 tokens) retrieval of the operational task state,
change tracking and the lifecycle management of the checkboxes.
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
    p_pulse = subparsers.add_parser("pulse", help="Instant compressed snapshot of the studio operational pulse")
    p_pulse.add_argument("--project", choices=["mars", "kot", "pm", "Studio"], help="Filter by project")
    p_pulse.add_argument("--json", action="store_true", help="JSON format output")

    # complete
    p_comp = subparsers.add_parser("complete", help="Mark a task as done (- [x])")
    p_comp.add_argument("query", help="Substring of the task name")
    p_comp.add_argument("--project", choices=["mars", "kot", "pm", "Studio"], help="Target project")

    # check
    subparsers.add_parser("check", help="Integrity check of the task database and boards")

    args = parser.parse_args()

    if args.command == "pulse" or not args.command:
        project = getattr(args, "project", None)
        pulse = TasksRouter.get_pulse(project)
        if getattr(args, "json", False):
            print(json.dumps(pulse, ensure_ascii=False, indent=2))
        else:
            proj_title = f" ({project.upper()})" if project else " (All projects)"
            print(f"=== ⚡ Studio production pulse{proj_title} ===")
            print(f"📋 Total open tasks: {pulse['pending_count']}")
            print(f"🔥 Urgent / burning: {pulse['urgent_count']}")
            print(f"✅ Completed: {pulse['completed_count']}")

            if pulse["urgent_tasks"]:
                print("\n🚨 Urgent tasks and blockers:")
                for t in pulse["urgent_tasks"]:
                    due_info = f" [due {t['due']}]" if t['due'] else ""
                    print(f"  • [{t['file']}] {t['title']}{due_info}")

            if pulse["regular_tasks_sample"]:
                print("\n📌 In progress (selection):")
                for t in pulse["regular_tasks_sample"]:
                    print(f"  - [{t['file']}] {t['title']}")

    elif args.command == "complete":
        res = TasksRouter.complete_task(args.query, getattr(args, "project", None))
        if res.get("status") == "success":
            print(f"✅ Task completed: {res['completed']}")
            print(f"  • Board: {res['board']}")
            print(f"  • Date: {res['date']}")
        else:
            print(f"❌ {res.get('message')}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "check":
        pulse = TasksRouter.get_pulse()
        print("🟢 [Tasks Bridge Status: OK]")
        print(f"  • Indexed open tasks: {pulse['pending_count']}")
        print(f"  • Completed tasks: {pulse['completed_count']}")
        print(f"  • SQLite database: and_os/var/task_vault.db")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
