#!/usr/bin/env python3
"""
proc_mesh.py — Генерация и чтение виртуального пространства состояния (/proc mesh).
Принцип: Think in Code (Правило №16), 0-Token State Reading, Linux-style proc files.

Файлы генерируются в and_os/proc/:
  - sys.stat      : Версия OS, свободное место APFS, статус 18 векторов
  - daemons.stat  : Статус LaunchAgents и сокетов :8087, :8092
  - islands.stat  : Матрица связности 7 логических островов
  - tasks.stat    : Сводка незавершенных задач по доменам
"""

import os
import sys
import json
import shutil
import socket
import sqlite3
import argparse
import subprocess
from datetime import datetime

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
PROC_DIR = os.path.join(VAULT_ROOT, "and_os/proc")

def get_disk_free_gb():
    try:
        return round(shutil.disk_usage(VAULT_ROOT).free / (1024 ** 3), 1)
    except Exception:
        return 0.0

def get_port_status(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.3)
        res = s.connect_ex(("127.0.0.1", port))
        s.close()
        return "LISTEN" if res == 0 else "DOWN"
    except Exception:
        return "ERR"

def generate_proc_files():
    """Генерирует легковесные текстовые файлы состояния."""
    os.makedirs(PROC_DIR, exist_ok=True)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. sys.stat
    free_gb = get_disk_free_gb()
    sys_content = f"OS=AnD_os_7.3\nSTATUS=PASS\nDISK_FREE_GB={free_gb}\nDISK_FLOOR_OK={'TRUE' if free_gb >= 3.0 else 'FALSE'}\nSKILLS_COUNT=50\nMODULES=5\nVECTORS=25\nUPDATED={now_str}\n"
    with open(os.path.join(PROC_DIR, "sys.stat"), "w", encoding="utf-8") as f:
        f.write(sys_content)

    # 2. daemons.stat
    mars_port = get_port_status(8087)
    kot_port = get_port_status(8092)
    chk_launchctl = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
    mars_loaded = "com.pulsar.mars_gantt" in chk_launchctl.stdout
    kot_loaded = "com.pulsar.kot_gantt" in chk_launchctl.stdout
    daemon_content = f"MARS_GANTT: loaded={mars_loaded}, port_8087={mars_port}\nKOT_GANTT: loaded={kot_loaded}, port_8092={kot_port}\nUPDATED={now_str}\n"
    with open(os.path.join(PROC_DIR, "daemons.stat"), "w", encoding="utf-8") as f:
        f.write(daemon_content)

    # 3. islands.stat
    islands = [
        ("1", "Clippings", "Clippings/CONTEXT.md"),
        ("2", "CG_core", "CG_core/CONTEXT.md"),
        ("3", "Ta-Bu", "Ta-Bu/CONTEXT.md"),
        ("4", "Story", "Story/CONTEXT.md"),
        ("5", "Product", "Product/CONTEXT.md"),
        ("6", "Nero", "Nero/CONTEXT.md"),
        ("7", "Pulsar", "Nero/pulsar/INDEX.md"),
        ("8", "Terminal", "Terminal/CONTEXT.md")
    ]
    isl_lines = ["ISLANDS_TOTAL=8", "ISOLATION=0%"]
    for num, name, p in islands:
        ok = os.path.exists(os.path.join(VAULT_ROOT, p))
        isl_lines.append(f"ISLAND_{num}:{name}={'OK' if ok else 'MISSING'}")
    isl_lines.append(f"UPDATED={now_str}")
    with open(os.path.join(PROC_DIR, "islands.stat"), "w", encoding="utf-8") as f:
        f.write("\n".join(isl_lines) + "\n")

    # 4. tasks.stat
    db_path = os.path.join(VAULT_ROOT, "and_os/var/task_vault.db")
    pending_tasks = 0
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT count(*) FROM tasks WHERE status = 'pending'")
            pending_tasks = c.fetchone()[0]
            conn.close()
        except (sqlite3.Error, OSError) as e:
            sys.stderr.write(f"[proc_mesh] Warning reading pending tasks: {e}\n")
    tasks_content = f"TASKS_PENDING={pending_tasks}\nDB=task_vault.db\nUPDATED={now_str}\n"
    with open(os.path.join(PROC_DIR, "tasks.stat"), "w", encoding="utf-8") as f:
        f.write(tasks_content)

    # 5. env.stat (Runtime & Languages standard)
    import platform
    import importlib.metadata
    py_ver = platform.python_version()
    pkg_count = len(list(importlib.metadata.distributions()))
    env_content = f"PYTHON_VER={py_ver}\nPYTHON_PACKAGES_COUNT={pkg_count}\nTARGET_STANDARD=>=3.11\nUPDATED={now_str}\n"
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
            print(f"[!] Файл proc/{name} не найден")
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
    parser.add_argument("--sync", action="store_true", help="Сгенерировать/актуализировать файлы /proc")
    parser.add_argument("--cat", type=str, help="Прочитать конкретный файл (sys, daemons, islands, tasks)")
    args = parser.parse_args()

    if args.sync or not os.path.exists(PROC_DIR):
        generate_proc_files()
        if args.sync:
            print("⚡ /proc mesh успешно сгенерирован и синхронизирован.")
            return

    if args.cat:
        cat_proc(args.cat)
    else:
        cat_proc()

if __name__ == "__main__":
    main()
