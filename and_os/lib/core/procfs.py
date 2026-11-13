#!/usr/bin/env python3
"""
procfs.py — Fast ProcFS / SysFS Generator for AnD os (and_os/proc/).
Part of AnD os Kernel Core (and_os/lib/core/).

Generates lightweight, sub-millisecond .stat snapshots for instant agent reading:
  - sys.stat: ~200 bytes, ultra-low token consumption (~40 tokens)
  - islands.stat: 8 islands health matrix
  - daemons.stat: active background services
  - tasks.stat: task metrics from SQLite/markdown

Principles: Token-efficiency (Rule №24), Think in Code (Rule №16).
"""

import os
import shutil
import socket
from datetime import datetime
from and_os.lib.core.vfs import DIR_PROC, VAULT_ROOT, AND_OS_ROOT
from and_os.lib.core.state import load_states

def update_procfs() -> dict:
    """Updates all files in and_os/proc/ and returns a summary dict."""
    os.makedirs(DIR_PROC, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. Disk & Memory Guard
    total, used, free = shutil.disk_usage(VAULT_ROOT)
    free_gb = round(free / (1024**3), 1)

    # 2. Daemon Ports Check
    daemons = {
        "terminal_web": {"port": 8099, "status": "DOWN"},
        "mars_gantt": {"port": 8087, "status": "DOWN"},
        "kot_gantt": {"port": 8092, "status": "DOWN"}
    }
    for name, d in daemons.items():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.05)
            if s.connect_ex(("127.0.0.1", d["port"])) == 0:
                d["status"] = "UP"

    # Check VFS Sentinel Daemon
    vfs_pid_file = os.path.join(AND_OS_ROOT, "var", "vfs_daemon.pid")
    vfs_up = False
    if os.path.exists(vfs_pid_file):
        try:
            with open(vfs_pid_file) as pf:
                pid = int(pf.read().strip())
            os.kill(pid, 0)
            vfs_up = True
        except (ValueError, OSError):
            vfs_up = False

    # 3. Write sys.stat (~200 bytes). VERSION and RULES_COUNT come from the
    # canonical SSoT (the 1.0 kernel versioning release, 13.11, declared I-1
    # exception, version-only: before this they were hardcoded literals of a
    # long-closed development series - a mesh format the banner gates
    # cannot see, which is exactly how the drift survived until F1).
    from and_os.lib.core.root_config import get_system_release
    release = get_system_release(VAULT_ROOT)
    sys_stat_path = os.path.join(DIR_PROC, "sys.stat")
    with open(sys_stat_path, "w", encoding="utf-8") as f:
        f.write(f"OS=AnD_os\n")
        f.write(f"VERSION={release.get('version', 'UNKNOWN')}\n")
        f.write(f"RULES_COUNT={release.get('rules_count', 'UNKNOWN')}\n")
        f.write(f"TIMESTAMP={now}\n")
        f.write(f"DISK_FREE_GB={free_gb}\n")
        f.write(f"RESOURCE_GUARD={'OK' if free_gb >= 3.0 else 'WARN_DISK_LOW'}\n")
        f.write(f"VFS_SENTINEL={'ACTIVE' if vfs_up else 'STANDBY'}\n")
        f.write(f"DAEMONS_UP={sum(1 for d in daemons.values() if d['status'] == 'UP')}/{len(daemons)}\n")
        f.write(f"STATUS=HEALTHY\n")

    # 4. Write daemons.stat
    daemons_stat_path = os.path.join(DIR_PROC, "daemons.stat")
    with open(daemons_stat_path, "w", encoding="utf-8") as f:
        f.write(f"# AnD os Daemons Status ({now})\n")
        for name, d in daemons.items():
            f.write(f"{name}:{d['port']}={d['status']}\n")

    # 5. Write islands.stat
    islands_stat_path = os.path.join(DIR_PROC, "islands.stat")
    states = load_states()
    with open(islands_stat_path, "w", encoding="utf-8") as f:
        f.write(f"# AnD os 8 Islands Matrix ({now})\n")
        f.write("1_knowledge=ACTIVE\n")
        f.write("2_cg_core=ACTIVE\n")
        f.write(f"3_ta_bu={states.get('ta_bu', {}).get('status', 'OK')}\n")
        f.write("4_story=ACTIVE\n")
        f.write(f"5_Studio={states.get('work_mars', {}).get('status', 'OK')}\n")
        f.write("6_and_os=SOVEREIGN_CORE\n")
        f.write(f"7_pulsar_3d=ACTIVE\n")
        f.write(f"8_terminal={'ACTIVE' if daemons['terminal_web']['status'] == 'UP' else 'STANDBY'}\n")

    return {
        "timestamp": now,
        "disk_free_gb": free_gb,
        "daemons": daemons,
        "sys_stat": sys_stat_path
    }

def read_sys_stat() -> str:
    """Reads sys.stat in one quick shot."""
    p = os.path.join(DIR_PROC, "sys.stat")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "STATUS=UNKNOWN"
