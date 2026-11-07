#!/usr/bin/env python3
"""
vfs_bridge.py — CLI Router and Bridge for VFS Subsystem in AnD os v8.1.
Part of AnD os Binary Bridges (and_os/bin/).

Commands:
  sys_cli.py vfs --status
  sys_cli.py vfs --find <query> [--island <name>] [--ext <ext>]
  sys_cli.py vfs --sync
  sys_cli.py vfs --start-daemon
  sys_cli.py vfs --stop-daemon
"""

import os
import sys
import subprocess
from datetime import datetime

BIN_DIR = os.path.dirname(os.path.realpath(__file__))
AND_OS_ROOT = os.path.abspath(os.path.join(BIN_DIR, ".."))
VAULT_ROOT = os.path.abspath(os.path.join(AND_OS_ROOT, ".."))
VAR_DIR = os.path.join(AND_OS_ROOT, "var")
PID_FILE = os.path.join(VAR_DIR, "vfs_daemon.pid")

# Add lib to sys.path
LIB_DIR = os.path.join(AND_OS_ROOT, "lib")
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

from vfs.vfs_engine import VFSEngine


def is_daemon_running() -> int:
    pid_candidates = [
        PID_FILE,
        os.path.expanduser("~/.and_os/var/vfs_daemon.pid")
    ]
    for pf in pid_candidates:
        if os.path.exists(pf):
            try:
                with open(pf, "r") as f:
                    pid = int(f.read().strip())
                os.kill(pid, 0)
                return pid
            except Exception:
                pass
    return 0


def cmd_status():
    engine = VFSEngine()
    stats = engine.get_vfs_stats()
    pid = is_daemon_running()
    
    resource_badge = ""
    if pid:
        try:
            res = subprocess.run(["ps", "-o", "rss,%cpu", "-p", str(pid)], capture_output=True, text=True)
            lines = res.stdout.strip().splitlines()
            if len(lines) > 1:
                parts = lines[1].split()
                rss_mb = round(int(parts[0]) / 1024, 2)
                cpu_pct = parts[1]
                resource_badge = f" [RAM: {rss_mb} MB | CPU: {cpu_pct}%]"
        except (ValueError, IndexError) as e:
            sys.stderr.write(f"[vfs_bridge] Warning parsing ps output: {e}\n")

    daemon_badge = f"🟢 ACTIVE (PID {pid}){resource_badge}" if pid else "⚪ INACTIVE (On-Demand Mode)"
    db_size_kb = round(os.path.getsize(stats["db_path"]) / 1024, 1) if os.path.exists(stats["db_path"]) else 0
    
    print(f"=== 🛰️ AnD os v8.1 Virtual File System (VFS Status) ===")
    print(f"📡 Статус демона: {daemon_badge}")
    print(f"📁 Всего файлов в индексе: {stats['total_files']} (Заметок: {stats['markdown_notes']})")
    print(f"💾 База состояний: {os.path.basename(stats['db_path'])} ({db_size_kb} KB)")
    print("\n🏝️ Распределение по Островам:")
    for isl, cnt in sorted(stats["islands_breakdown"].items()):
        print(f"  • {isl}: {cnt} файлов")


def cmd_find(query: str, island: str = None, ext: str = None, limit: int = 15):
    engine = VFSEngine()
    results = engine.find_files(query=query, island=island, ext=ext, limit=limit)
    
    print(f"=== 🔍 Результаты VFS поиска по запросу '{query or '*'}' (найдено {len(results)}) ===")
    if not results:
        print("Ничего не найдено.")
        return
        
    for r in results:
        title_str = f" «{r['title']}»" if r["title"] else ""
        tags_str = f" [{r['tags']}]" if r["tags"] else ""
        print(f"  • [[{r['rel_path']}]] ({r['island']}){title_str}{tags_str}")


def cmd_sync():
    engine = VFSEngine()
    print("🔄 Запуск полной синхронизации VFS индекса...")
    res = engine.bootstrap_scan(VAULT_ROOT)
    print(f"✅ VFS синхронизирован: {res['scanned']} файлов за {res['elapsed_seconds']} сек.")


def cmd_start_daemon():
    pid = is_daemon_running()
    if pid:
        print(f"⚠️ VFS Daemon уже запущен (PID {pid}).")
        return
    daemon_script = os.path.join(AND_OS_ROOT, "sbin/vfs_daemon.py")
    log_file = os.path.join(VAR_DIR, "vfs_daemon.log")
    out = open(log_file, "a", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, daemon_script, "--watch"],
        stdin=subprocess.DEVNULL,
        stdout=out,
        stderr=out,
        start_new_session=True
    )
    print(f"🚀 VFS Daemon запущен в фоне (PID {proc.pid}). Лог: {os.path.relpath(log_file, VAULT_ROOT)}")


def cmd_stop_daemon():
    daemon_script = os.path.join(AND_OS_ROOT, "sbin/vfs_daemon.py")
    subprocess.run([sys.executable, daemon_script, "--stop"])


def cmd_pulsar():
    from vfs.pulsar_bridge import PulsarStateBridge
    bridge = PulsarStateBridge()
    projs = bridge.scan_and_sync()
    
    print(f"=== 🚀 Матрица Модулей и Сервисов Pulsar Space ({len(projs)} проектов) ===")
    for p in projs:
        act = "🟢" if p["is_active"] else "⚪"
        port = f":{p['port']}" if p["port"] else "no-port"
        cache_status = f" | Кэш: {p['cache_status']}" if p["cache_file"] else ""
        
        score = p.get("compliance_score", 0)
        issues = p.get("compliance_issues", "")
        if score == 100:
            comp_badge = "🟢 100% OK"
        elif score >= 75:
            comp_badge = f"🟡 {score}% WRN"
        else:
            comp_badge = f"🔴 {score}% ERR"
            
        print(f"  {act} [{p['category']:17}] {p['name']:24} ({port:7}) [{comp_badge}]{cache_status}")
        if issues:
            for issue in issues.split(" | "):
                if issue.strip():
                    print(f"      ⚠️  {issue.strip()}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AnD os VFS CLI Bridge")
    parser.add_argument("--status", action="store_true", help="Print VFS status")
    parser.add_argument("--pulsar", action="store_true", help="Print Pulsar Space modules and services matrix")
    parser.add_argument("--find", type=str, help="Search query")
    parser.add_argument("--island", type=str, help="Filter by island")
    parser.add_argument("--ext", type=str, help="Filter by extension")
    parser.add_argument("--sync", action="store_true", help="Sync VFS state")
    parser.add_argument("--start", action="store_true", help="Start background daemon")
    parser.add_argument("--stop", action="store_true", help="Stop background daemon")
    args = parser.parse_args()

    if args.status:
        cmd_status()
    elif args.pulsar:
        cmd_pulsar()
    elif args.find is not None:
        cmd_find(args.find, island=args.island, ext=args.ext)
    elif args.sync:
        cmd_sync()
    elif args.start:
        cmd_start_daemon()
    elif args.stop:
        cmd_stop_daemon()
    else:
        cmd_status()

