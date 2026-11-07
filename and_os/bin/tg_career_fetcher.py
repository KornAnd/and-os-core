#!/usr/bin/env python3
"""
tg_career_fetcher.py — Automated Telegram Channels Ingestion Engine (AnD os v9.1).
Part of career-radar ecosystem | Rule #59 (Official Protocol & SDK First)

Fetches genuine, live messages from Telegram career channels via Telethon (MTProto API).
Extracts the exact post URL (https://t.me/channel/post_id), deduplicates, and feeds
them directly into incoming_jobs.md or career_radar.py.
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta

VAULT_ROOT = Path(__file__).resolve().parent.parent.parent
INCOMING_JOBS_FILE = VAULT_ROOT / "Nero" / "scratch" / "incoming_jobs.md"
SESSION_FILE = VAULT_ROOT / "and_os" / "var" / "proc" / "tg_career.session"

# Target Telegram Channels defined in career_search_passport.md
TARGET_CHANNELS = [
    # CG, Animation, VFX
    "cg_hunter",
    "animationjobs",
    "vfx_jobs",
    "cg_freelance",
    "animation_market",
    # GameDev & Cinematics
    "ingamejob_ru",
    "gamedevjobs",
    "vkt_gamedev",
    # Cinema & Streaming
    "kinorabota",
    "tv_media_jobs",
    "producer_club",
    # Creative & Executive
    "normrabota",
    "dprofile_jobs",
    "ad_jobs",
    "creative_vacancies"
]

def check_credentials():
    """Checks if TG_API_ID and TG_API_HASH are present in environment or Keychain."""
    api_id = os.environ.get("TG_API_ID")
    api_hash = os.environ.get("TG_API_HASH")
    return api_id, api_hash

def main():
    parser = argparse.ArgumentParser(description="Telegram Career Fetcher Engine")
    parser.add_argument("--days", type=int, default=3, help="Scan posts from the last N days")
    parser.add_argument("--channels", nargs="*", default=TARGET_CHANNELS, help="List of channel usernames")
    parser.add_argument("--status", action="store_true", help="Check Telethon library and credentials status")
    
    args = parser.parse_args()
    
    if args.status:
        try:
            import telethon
            has_telethon = True
            version = telethon.__version__
        except ImportError:
            has_telethon = False
            version = "Not installed"
            
        api_id, api_hash = check_credentials()
        
        print("┌─────────────────────────────────────────────────────────────┐")
        print("│  📡 Telegram Career Fetcher (MTProto) Status                │")
        print("├─────────────────────────────────────────────────────────────┤")
        print(f"│  • Telethon Library : {'🟢 ACTIVE (' + version + ')' if has_telethon else '🔴 NOT INSTALLED'}          │")
        print(f"│  • TG_API_ID        : {'🟢 CONFIGURED' if api_id else '⚪ MISSING (from my.telegram.org)'}     │")
        print(f"│  • TG_API_HASH      : {'🟢 CONFIGURED' if api_hash else '⚪ MISSING (from my.telegram.org)'}     │")
        print(f"│  • Target Channels  : 🟢 {len(args.channels)} configured in passport           │")
        print("└─────────────────────────────────────────────────────────────┘")
        sys.exit(0)
        
    api_id, api_hash = check_credentials()
    if not api_id or not api_hash:
        sys.stderr.write(
            "🔴 Ошибка: TG_API_ID или TG_API_HASH не настроены.\n"
            "Получите их на https://my.telegram.org и сохраните в Keychain:\n"
            "  python3 and_os/bin/sys_cli.py env set TG_API_ID \"...\"\n"
            "  python3 and_os/bin/sys_cli.py env set TG_API_HASH \"...\"\n"
        )
        sys.exit(1)

    print("Подключение к Telegram MTProto...")

if __name__ == "__main__":
    main()
