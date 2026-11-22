#!/usr/bin/env python3
"""
link_guard.py — Vault-wide wikilink integrity gate (CLI).
AnD os v1.2.0 (R-2, 20.11). Named per the AGENTS.md Fast-Track contract
("sys_cli verify and link_guard.py"); core scanner is shared with the
Health Grid LinkProbe (and_os/lib/health_grid/link_scan.py).

Usage:
  link_guard.py [--json] [--no-cache]

Exit codes: 0 = clean (broken links only in historical records),
1 = dead links in live documents, 2 = usage error.
"""

import argparse
import json
import os
import sys

sys.dont_write_bytecode = True

VAULT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, VAULT_ROOT)

from and_os.lib.health_grid.link_scan import scan_vault  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Vault-wide wikilink integrity gate (Obsidian resolution semantics)")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    parser.add_argument("--no-cache", action="store_true", help="Force a full rescan")
    args = parser.parse_args()

    scan = scan_vault(VAULT_ROOT, use_cache=not args.no_cache)
    broken = scan.get("broken", [])
    hist = scan.get("historical_broken", 0)
    assets = scan.get("asset_broken", 0)

    if args.json:
        print(json.dumps(scan, ensure_ascii=False, indent=2))
    else:
        print("=" * 60)
        print(f"🔗 Link Guard — vault wikilink integrity (AnD os v1.2.0)")
        print("=" * 60)
        print(f"  Files scanned : {scan['files_scanned']}")
        print(f"  Links scanned : {scan['links_scanned']}")
        print(f"  Dead (live)   : {len(broken)}  (BLOCKED)")
        print(f"  Dead (history): {hist}  (forward-only, advisory)")
        print(f"  Dead (assets) : {assets}  (lost attachments, advisory)")
        print(f"  Cache         : {'hit' if scan.get('cached') else 'full scan'}"
              f" ({scan['elapsed_sec']}s)")
        if broken:
            print()
            for entry in broken[:25]:
                print(f"  ❌ {entry['file']}")
                print(f"       [[{entry['link']}]] -> target not found")
            if len(broken) > 25:
                print(f"  ... and {len(broken) - 25} more")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
