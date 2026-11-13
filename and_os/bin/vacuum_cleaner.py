#!/usr/bin/env python3
"""
vacuum_cleaner.py — AnD os System Sanitizer & Junk Collector (v1.0.0).
Cleans the Obsidian Vault and the Pulsar ecosystem from junk artifacts:
  - .DS_Store, Icon\r
  - Intermediate backups *.bak, *.tmp, *~
  - Python bytecode and caches: __pycache__, *.pyc, *.pyo, .pytest_cache
  - Temporary build artifacts

Usage:
  python3 vacuum_cleaner.py --dry-run
  python3 vacuum_cleaner.py --target [all|vault|pulsar] [--dry-run]
"""

import os
import sys
import shutil
import argparse

VAULT_ROOT = os.getenv("AND_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
PULSAR_ROOT = os.getenv("PULSAR_ROOT", os.path.expanduser("./pulsar"))
PULSAR_APPS = os.getenv("PULSAR_APPS", os.path.expanduser("~/Pulsar_Apps"))

TRASH_PATTERNS = {
    "exact_files": {".DS_Store"},
    "extensions": {".bak", ".tmp", ".pyc", ".pyo"},
    "exact_dirs": {"__pycache__", ".pytest_cache"}
}

SAFE_SKIP_DIRS = {".git", ".space", ".obsidian"}

def clean_directory(root_path, dry_run=False):
    if not os.path.exists(root_path):
        return {"files_removed": 0, "dirs_removed": 0, "bytes_freed": 0, "errors": 0}

    files_removed = 0
    dirs_removed = 0
    bytes_freed = 0
    errors = 0

    for current_dir, dirs, files in os.walk(root_path, topdown=True):
        # Skip safe version-control and internal directories
        dirs[:] = [d for d in dirs if d not in SAFE_SKIP_DIRS]

        # 1. Clean directories
        for d in list(dirs):
            if d in TRASH_PATTERNS["exact_dirs"]:
                dir_path = os.path.join(current_dir, d)
                try:
                    size = sum(os.path.getsize(os.path.join(dirpath, f)) 
                               for dirpath, _, filenames in os.walk(dir_path) for f in filenames if os.path.exists(os.path.join(dirpath, f)))
                    if not dry_run:
                        shutil.rmtree(dir_path, ignore_errors=True)
                    dirs_removed += 1
                    bytes_freed += size
                    dirs.remove(d)
                except Exception:
                    errors += 1

        # 2. Clean files
        for f in files:
            file_path = os.path.join(current_dir, f)
            _, ext = os.path.splitext(f)
            is_trash = (f in TRASH_PATTERNS["exact_files"]) or (ext.lower() in TRASH_PATTERNS["extensions"])

            if is_trash:
                try:
                    size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                    if not dry_run:
                        os.remove(file_path)
                    files_removed += 1
                    bytes_freed += size
                except Exception:
                    errors += 1

    return {
        "files_removed": files_removed,
        "dirs_removed": dirs_removed,
        "bytes_freed": bytes_freed,
        "errors": errors
    }

def main():
    parser = argparse.ArgumentParser(description="AnD os System Vacuum Cleaner")
    parser.add_argument("--target", choices=["all", "vault", "pulsar"], default="all", help="Target zone to vacuum")
    parser.add_argument("--dry-run", action="store_true", help="Scan and calculate without deleting")
    args = parser.parse_args()

    targets = []
    if args.target in ("all", "vault"):
        targets.append(("Vault (Obsidian / and_os)", VAULT_ROOT))
    if args.target in ("all", "pulsar"):
        targets.append(("Pulsar Workspace", PULSAR_ROOT))
        if os.path.exists(PULSAR_APPS):
            targets.append(("Pulsar Apps", PULSAR_APPS))

    mode_str = "🔍 [DRY RUN SCAN]" if args.dry_run else "🧹 [VACUUM CLEANING]"
    print(f"{mode_str} Starting system sanitary maintenance...")

    total_files = 0
    total_dirs = 0
    total_bytes = 0

    for name, path in targets:
        res = clean_directory(path, dry_run=args.dry_run)
        total_files += res["files_removed"]
        total_dirs += res["dirs_removed"]
        total_bytes += res["bytes_freed"]
        kb_freed = res["bytes_freed"] / 1024.0
        print(f"  • {name}: {res['files_removed']} files, {res['dirs_removed']} cache dirs ({kb_freed:.1f} KB)")

    total_kb = total_bytes / 1024.0
    action_verb = "detected" if args.dry_run else "reclaimed"
    print(f"✨ Finished: {total_files} files, {total_dirs} directories {action_verb} ({total_kb:.1f} KB freed).")

if __name__ == "__main__":
    main()
