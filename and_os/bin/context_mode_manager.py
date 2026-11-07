#!/usr/bin/env python3
"""
context_mode_manager.py - Context Mode Switcher for AnD os v8.5.
Manages active behavioral presets (dev, research, review) for LLM agents.
"""

import os
import sys
import json
import time
import argparse
from typing import Dict, Any, List, Optional

sys.dont_write_bytecode = True

VALID_MODES = ["dev", "research", "review"]


class ContextModeManager:
    def __init__(self, vault_root: str):
        self.vault_root = os.path.abspath(vault_root)
        self.modes_dir = os.path.join(self.vault_root, "and_os", "etc", "modes")
        self.state_file = os.path.join(self.vault_root, "and_os", "var", "current_mode.json")
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)

    def get_current_mode(self) -> str:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("active_mode", "dev")
            except Exception:
                pass
        return "dev"

    def set_mode(self, mode: str) -> Dict[str, Any]:
        mode = mode.lower().strip()
        if mode not in VALID_MODES:
            raise ValueError(f"Invalid mode '{mode}'. Choose from: {', '.join(VALID_MODES)}")

        record = {
            "active_mode": mode,
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": time.time()
        }

        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)

        return record

    def get_mode_instruction(self, mode: Optional[str] = None) -> str:
        target_mode = mode or self.get_current_mode()
        path = os.path.join(self.modes_dir, f"{target_mode}.md")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return f"Context mode '{target_mode}' instruction not found."


def main():
    parser = argparse.ArgumentParser(description="AnD os Context Mode Manager")
    parser.add_argument("action", nargs="?", default="get", choices=["get", "set", "show", "list"], help="Action: get, set, show, list")
    parser.add_argument("mode", nargs="?", help="Target mode name (dev, research, review)")

    args = parser.parse_args()
    vault_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    mgr = ContextModeManager(vault_root)

    if args.action == "get":
        cur = mgr.get_current_mode()
        print(f"🎯 Текущий активный режим контекста: {cur.upper()}")
    elif args.action == "set":
        if not args.mode:
            print("❌ Укажите режим: dev, research или review", file=sys.stderr)
            sys.exit(1)
        try:
            res = mgr.set_mode(args.mode)
            print(f"✅ Режим контекста переключен на: {res['active_mode'].upper()} ({res['updated_at']})")
        except ValueError as err:
            print(f"❌ {err}", file=sys.stderr)
            sys.exit(1)
    elif args.action == "show":
        cur = mgr.get_current_mode()
        instr = mgr.get_mode_instruction(args.mode)
        print(f"--- [АКТИВНЫЙ ПРЕСЕТ: {cur.upper()}] ---\n")
        print(instr)
    elif args.action == "list":
        cur = mgr.get_current_mode()
        print("📋 ДОСТУПНЫЕ РЕЖИМЫ КОНТЕКСТА:")
        for m in VALID_MODES:
            mark = "🟢 (АКТИВЕН)" if m == cur else "⚪"
            print(f"  • {m:<10} {mark}")


if __name__ == "__main__":
    main()
