#!/usr/bin/env python3
"""
proc_mesh.py — Generation and reading of the virtual state space (/proc mesh).
Principle: Think in Code (Rule #16), 0-Token State Reading, Linux-style proc files.

On-demand service (Andrey's decision 13.11, audit F1): run via
`sys_cli daemon trigger proc_mesh` — the 60s cron cadence is retired.

Files are generated in and_os/proc/ (single canonical writer — the kernel
update_procfs() is composed for the shared files, this script adds its own):
  - sys.stat      : kernel — canonical version, rules count, disk, daemons
  - daemons.stat  : kernel — live :8087/:8092/:8099 sockets status
  - islands.stat  : kernel — islands state matrix
  - tasks.stat    : this script — live pending task count (task_vault.db)
  - env.stat      : this script — runtime standard + live SKILL.md count
"""

import os
import sys
import sqlite3
import argparse
from datetime import datetime

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if VAULT_ROOT not in sys.path:
    sys.path.insert(0, VAULT_ROOT)
PROC_DIR = os.path.join(VAULT_ROOT, "and_os/proc")

def count_skills():
    """The live SKILL.md count under and_os/lib/skills/ (0-token metric)."""
    skills_dir = os.path.join(VAULT_ROOT, "and_os", "lib", "skills")
    try:
        return sum(
            1
            for entry in os.scandir(skills_dir)
            if entry.is_dir()
            and os.path.isfile(os.path.join(entry.path, "SKILL.md"))
        )
    except OSError as err:
        sys.stderr.write(f"[proc_mesh] Warning counting skills: {err}\n")
        return 0


def count_pending_tasks(db_path):
    """Counts pending tasks in task_vault.db (audit R4, P2, R4-PROC-2).

    The live schema marks completion with `is_completed INTEGER`
    (0 = pending, 1 = done); the legacy `status = 'pending'` column
    does not exist and failed every sync with "no such column: status".
    A missing database returns 0 silently; a read error is announced on
    stderr (never silent) and also returns 0.
    """
    if not os.path.exists(db_path):
        return 0
    try:
        conn = sqlite3.connect(db_path)
        try:
            c = conn.cursor()
            c.execute("SELECT count(*) FROM tasks WHERE is_completed = 0")
            return int(c.fetchone()[0])
        finally:
            conn.close()
    except (sqlite3.Error, OSError) as e:
        sys.stderr.write(f"[proc_mesh] Warning reading pending tasks: {e}\n")
        return 0

def generate_proc_files() -> bool:
    """Generates the virtual /proc mesh (on-demand service, 13.11).

    Single canonical writer: composes on the kernel update_procfs()
    (sys.stat / daemons.stat / islands.stat — the kernel is the only
    generator that reads the version and the rules count from the
    canonical SSoT; before the 13.11 on-demand decision this script was a
    second writer with hardcoded 7.x literals that overwrote the kernel
    output every 60s, audit F1). Adds the two files the kernel does not
    write: tasks.stat (live pending count) and env.stat (runtime standard
    + the live SKILL.md count).
    """
    os.makedirs(PROC_DIR, exist_ok=True)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        from and_os.lib.core.procfs import update_procfs
        update_procfs()
    except (ImportError, OSError, ValueError) as err:
        sys.stderr.write(f"[proc_mesh] Error: kernel procfs generation failed: {err}\n")
        return False

    # 1. tasks.stat (proc_mesh-only file)
    db_path = os.path.join(VAULT_ROOT, "and_os", "var", "task_vault.db")
    pending_tasks = count_pending_tasks(db_path)
    tasks_content = f"TASKS_PENDING={pending_tasks}\nDB=task_vault.db\nUPDATED={now_str}\n"
    with open(os.path.join(PROC_DIR, "tasks.stat"), "w", encoding="utf-8") as f:
        f.write(tasks_content)

    # 2. env.stat (Runtime & Languages standard + live skill count)
    import platform
    import importlib.metadata
    py_ver = platform.python_version()
    pkg_count = len(list(importlib.metadata.distributions()))
    env_content = (
        f"PYTHON_VER={py_ver}\nPYTHON_PACKAGES_COUNT={pkg_count}\n"
        f"SKILLS_COUNT={count_skills()}\nTARGET_STANDARD=>=3.11\nUPDATED={now_str}\n"
    )
    with open(os.path.join(PROC_DIR, "env.stat"), "w", encoding="utf-8") as f:
        f.write(env_content)

    return True

def cat_proc(name=None):
    if not os.path.exists(PROC_DIR):
        generate_proc_files()
        
    if name:
        target = os.path.join(PROC_DIR, f"{name}.stat" if not name.endswith(".stat") else name)
        if os.path.exists(target):
            with open(target, "r", encoding="utf-8") as f:
                print(f.read().strip())
        else:
            print(f"[!] proc/{name} file not found")
    else:
        print("=== 📂 /proc Virtual Mesh (Zero-Token State Files) ===")
        for fn in sorted(os.listdir(PROC_DIR)):
            if fn.endswith(".stat"):
                fpath = os.path.join(PROC_DIR, fn)
                with open(fpath, "r", encoding="utf-8") as f:
                    print(f"--- [proc/{fn}] ---")
                    print(f.read().strip())

def main():
    parser = argparse.ArgumentParser(description="Virtual /proc mesh generator & reader")
    parser.add_argument("--sync", action="store_true", help="Generate/update the /proc files")
    parser.add_argument("--cat", type=str, help="Read a specific file (sys, daemons, islands, tasks)")
    args = parser.parse_args()

    if args.sync or not os.path.exists(PROC_DIR):
        if not generate_proc_files():
            print("[!] /proc mesh generation failed (notice on stderr)")
            sys.exit(1)
        if args.sync:
            print("⚡ /proc mesh generated and synchronized successfully.")
            return

    if args.cat:
        cat_proc(args.cat)
    else:
        cat_proc()

if __name__ == "__main__":
    main()
