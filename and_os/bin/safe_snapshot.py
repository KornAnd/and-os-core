#!/usr/bin/env python3
"""
safe_snapshot.py — Management of system state snapshots (APFS Local Snapshot & State Snapshots).
Principles: APFS Native CoW (Rule #42, #43), Kernel Panic Recovery, Idempotency.
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
from datetime import datetime

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SNAPSHOT_DIR = os.path.join(VAULT_ROOT, ".archive/snapshots")

def create_apfs_snapshot(comment=""):
    """Creates a native APFS volume snapshot via tmutil."""
    print("📸 Creating the hardware APFS Local Snapshot (Copy-on-Write)...")
    try:
        res = subprocess.run(["tmutil", "localsnapshot"], capture_output=True, text=True)
        if res.returncode == 0:
            lines = res.stdout.strip().split("\n")
            snap_tag = lines[-1] if lines else "OK"
            print(f"  [OK] APFS snapshot created successfully: {snap_tag}")
            if comment:
                print(f"  [NOTE] Snapshot comment: {comment}")
            return True, snap_tag
        else:
            print(f"  [WARN] APFS snapshot creation error: {res.stderr.strip()}")
            return False, res.stderr.strip()
    except Exception as e:
        print(f"  [!] tmutil exception: {e}")
        return False, str(e)

def list_apfs_snapshots():
    """Prints the list of existing local APFS snapshots."""
    try:
        res = subprocess.run(["tmutil", "listlocalsnapshots", "/"], capture_output=True, text=True)
        if res.returncode == 0:
            print("=== 📋 List of local APFS snapshots (disk /) ===")
            print(res.stdout.strip())
        else:
            print(f"  [WARN] Failed to fetch the list: {res.stderr.strip()}")
    except Exception as e:
        print(f"  [!] Error: {e}")

def create_manifest_snapshot(comment=""):
    """Creates a fast micro-snapshot of the critical kernel manifests (.archive/snapshots)."""
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_backup_dir = os.path.join(SNAPSHOT_DIR, f"snap_{ts}")
    os.makedirs(target_backup_dir, exist_ok=True)
    
    critical_files = [
        "SYSTEM.md",
        "system.json",
        ".opencode/rules.md",
        "and_os/etc/SYSTEM_MAP.md",
        "and_os/var/domain_states.json"
    ]
    
    copied = 0
    for rel in critical_files:
        src = os.path.join(VAULT_ROOT, rel)
        if os.path.exists(src):
            dst = os.path.join(target_backup_dir, os.path.basename(rel))
            shutil.copy2(src, dst)
            copied += 1
            
    meta = {
        "timestamp": ts,
        "comment": comment or "Automatic pre-operation snapshot",
        "files_count": copied
    }
    with open(os.path.join(target_backup_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
        
    print(f"💾 Manifest micro-snapshot saved: .archive/snapshots/snap_{ts} ({copied} files).")
    return target_backup_dir

def main():
    parser = argparse.ArgumentParser(description="APFS & Core State Snapshot Manager (AnD os v1.0.0)")
    parser.add_argument("action", choices=["create", "list", "micro"], help="Snapshot action")
    parser.add_argument("--comment", "-m", type=str, default="", help="Snapshot description")
    args = parser.parse_args()

    if args.action == "create":
        create_apfs_snapshot(args.comment)
        create_manifest_snapshot(args.comment)
    elif args.action == "list":
        list_apfs_snapshots()
    elif args.action == "micro":
        create_manifest_snapshot(args.comment)

if __name__ == "__main__":
    main()
