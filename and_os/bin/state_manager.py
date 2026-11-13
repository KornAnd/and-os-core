#!/usr/bin/env python3
"""
state_manager.py (v1.2.0) — Unified Domain State Manager (IPC Bus).
Manages, persists, and reconciles lean JSON states across core domains:
  - health (metrics & active protocol, strict 7-day gate)
  - work_mars (Sprint production progress)
  - work_kot (Post-production stage)
  - ta_bu (Startup development status)
  - finance (Read-only / Manual updates by Andrey only)

Usage:
  python3 state_manager.py --get health
  python3 state_manager.py --get-all --json
  python3 state_manager.py --sync-auto
  python3 state_manager.py --set health --key status --val STABLE
"""

import os
import sys
import re
import json
import argparse
from datetime import datetime

VAULT_ROOT = os.getenv("AND_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
STATE_CACHE_PATH = os.path.join(VAULT_ROOT, "and_os/var/domain_states.json")

DEFAULT_STATES = {
    "health": {
        "domain": "health",
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "status": "STABLE",
        "active_protocol": "UC Maintenance",
        "key_metrics": {"vo2max": 52, "weight": 76.5}
    },
    "work_mars": {
        "domain": "work_mars",
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "status": "PRODUCTION",
        "active_sprint": "Sprint 42",
        "completion_rate": "84%"
    },
    "work_kot": {
        "domain": "work_kot",
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "status": "POST_PRODUCTION",
        "active_stage": "Lighting & Render"
    },
    "ta_bu": {
        "domain": "ta_bu",
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "status": "DEVELOPMENT",
        "active_focus": "Modular Soft Core"
    },
    "finance": {
        "domain": "finance",
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "status": "COMPLIANT",
        "tax_mode": "NPD / IP"
    }
}

def load_states():
    if not os.path.exists(STATE_CACHE_PATH):
        os.makedirs(os.path.dirname(STATE_CACHE_PATH), exist_ok=True)
        save_states(DEFAULT_STATES)
        return DEFAULT_STATES
    try:
        with open(STATE_CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_STATES

def save_states(states):
    os.makedirs(os.path.dirname(STATE_CACHE_PATH), exist_ok=True)
    with open(STATE_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(states, f, ensure_ascii=False, indent=2)

def extract_frontmatter(file_path):
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        if not content.startswith("---"):
            return {}
        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}
        yaml_lines = parts[1].strip().splitlines()
        data = {}
        for line in yaml_lines:
            if ":" in line:
                k, v = line.split(":", 1)
                data[k.strip()] = v.strip().strip('"').strip("'")
        return data
    except Exception:
        return {}

def auto_sync_states():
    states = load_states()
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")

    # 1. Health: Strict Weekly Interval (7 Days Gate)
    # Health updates are controlled: at most once every 7 days
    health_last_updated = states.get("health", {}).get("last_updated")
    allow_health_sync = False
    if not health_last_updated:
        allow_health_sync = True
    else:
        try:
            last_date = datetime.strptime(health_last_updated, "%Y-%m-%d")
            if (today - last_date).days >= 7:
                allow_health_sync = True
        except ValueError:
            allow_health_sync = True

    if allow_health_sync:
        health_md = os.path.join(VAULT_ROOT, "Nero/profile/health/my/health.md")
        h_data = extract_frontmatter(health_md)
        if h_data:
            states["health"]["status"] = h_data.get("status", states["health"].get("status", "STABLE"))
            states["health"]["last_updated"] = today_str

    # 2. Finance: STRICTLY MANUAL — AUTO-SYNC FORBIDDEN
    # Finances are maintained by Andrey manually only. Any auto-update is blocked.
    if "finance" in states:
        states["finance"]["auto_sync"] = "DISABLED (Manual updates only by Andrey)"

    # 3. Work Mars (Dynamic update from production file)
    mars_md = os.path.join(VAULT_ROOT, "Nero/work/mars/mars.md")
    m_data = extract_frontmatter(mars_md)
    if m_data:
        states["work_mars"]["status"] = m_data.get("status", states["work_mars"].get("status", "PRODUCTION"))
        states["work_mars"]["last_updated"] = today_str

    # 4. Work Kot (Dynamic update from production file)
    kot_md = os.path.join(VAULT_ROOT, "Nero/work/kot/kot.md")
    k_data = extract_frontmatter(kot_md)
    if k_data:
        states["work_kot"]["status"] = k_data.get("status", states["work_kot"].get("status", "POST_PRODUCTION"))
        states["work_kot"]["last_updated"] = today_str

    save_states(states)
    return states

def main():
    parser = argparse.ArgumentParser(description="State Manager Module")
    parser.add_argument("--get", type=str, help="Get the state of a specific domain")
    parser.add_argument("--get-all", action="store_true", help="Get the state of all domains")
    parser.add_argument("--sync-auto", action="store_true", help="Auto-sync states from .md note frontmatter")
    parser.add_argument("--set", type=str, help="Set the domain to modify")
    parser.add_argument("--key", type=str, help="State key")
    parser.add_argument("--val", type=str, help="State value")
    parser.add_argument("--json", action="store_true", help="Format the output as JSON")

    args = parser.parse_args()

    if args.sync_auto:
        states = auto_sync_states()
        print(json.dumps({"status": "SUCCESS", "synced_states": states}, ensure_ascii=False, indent=2))
        return

    states = load_states()

    if args.get:
        domain_state = states.get(args.get, {"error": f"Domain {args.get} not found"})
        print(json.dumps(domain_state, ensure_ascii=False, indent=2))
    elif args.get_all:
        print(json.dumps(states, ensure_ascii=False, indent=2))
    elif args.set and args.key and args.val:
        if args.set not in states:
            states[args.set] = {"domain": args.set}
        states[args.set][args.key] = args.val
        states[args.set]["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        save_states(states)
        print(json.dumps({"status": "SUCCESS", "updated": states[args.set]}, ensure_ascii=False, indent=2))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
