#!/usr/bin/env python3
"""
sys_bus.py — CLI Adapter for AnD os Canonical Event Journal.
Part of AnD os System Binaries (and_os/bin/).

Delegates 100% of journal writes and reads to the canonical and_os.lib.core.bus engine.
Maintains full backward compatibility for CLI commands:
  python3 and_os/bin/sys_bus.py emit --type FILE_CHANGED --payload '{"file": "x.md"}'
  python3 and_os/bin/sys_bus.py list -n 20
  python3 and_os/bin/sys_bus.py clear
"""

import os
import sys
import json
import argparse
from typing import Optional

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if VAULT_ROOT not in sys.path:
    sys.path.insert(0, VAULT_ROOT)

from and_os.lib.core.bus import emit_event, get_recent_events, clear_events


def emit(event_type: str, payload=None, source: str = "cli"):
    """Backward-compatible emit method delegating to canonical core bus."""
    return emit_event(event_type=event_type, payload=payload, source=source)


def list_events(count: int = 20, event_type: Optional[str] = None):
    """Backward-compatible list method."""
    return get_recent_events(limit=count, event_type=event_type)


def main():
    parser = argparse.ArgumentParser(description="AnD os Canonical Event Journal CLI")
    subparsers = parser.add_subparsers(dest="command", help="Bus commands")

    p_emit = subparsers.add_parser("emit", help="Publish an event to the journal")
    p_emit.add_argument("--type", "-t", required=True, help="Event type (e.g. FILE_CHANGED, TASK_DONE)")
    p_emit.add_argument("--payload", "-p", default="{}", help="JSON string or a message")
    p_emit.add_argument("--source", "-s", default="cli", help="Event source")

    p_list = subparsers.add_parser("list", help="Show the latest events")
    p_list.add_argument("-n", "--count", type=int, default=20, help="Number of lines")
    p_list.add_argument("--type", "-t", default=None, help="Filter by type")

    subparsers.add_parser("clear", help="Clear the event journal")

    args = parser.parse_args()

    if args.command == "emit":
        rec = emit(args.type, args.payload, source=args.source)
        print(f"🟢 Event emitted [{rec['event_id']}]: {rec['type']} from {rec['source']}")
    elif args.command == "list":
        events = list_events(args.count, args.type)
        if not events:
            print("⚪ The event journal is empty.")
            return
        for e in events:
            print(f"[{e.get('timestamp_utc', e.get('timestamp'))}] {e.get('type'):15} | {e.get('source'):12} | {json.dumps(e.get('payload', {}), ensure_ascii=False)}")
    elif args.command == "clear":
        if clear_events():
            print("🟢 The event journal has been cleared.")
        else:
            print("🔴 Error while clearing the journal.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
