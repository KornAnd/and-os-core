#!/usr/bin/env python3
"""
sync_preflight.py — Пре-полетный сканер изменений и синхронизатор структуры AnD os.
Правило №47: Pre-Flight Context & Cross-Chat Delta Synchronization Gate.

Сканирует:
1. Новые и модифицированные файлы в Obsidian Vault и Pulsar за последние N часов.
2. Дельту между and_os/opt/terminal и WORK/pulsar/AND_Terminal (код терминала).
3. Актуальность файлов состояния в and_os/proc/.
4. Сводный компактный отчет (<300 токенов) для агента перед запуском задачи.
"""

import os
import sys
import time
import json
import shutil
from typing import Dict, List, Any

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
AND_OS_ROOT = os.path.join(VAULT_ROOT, "and_os")
try:
    from and_os.lib.core.root_config import resolve_pulsar_root
    PULSAR_ROOT = resolve_pulsar_root() or os.path.expanduser("~/Yandex.Disk.localized/WORK/pulsar")
except Exception:
    PULSAR_ROOT = os.path.expanduser("~/Yandex.Disk.localized/WORK/pulsar")

IGNORE_SUBSTR = [
    ".git", "__pycache__", "node_modules", ".cache", ".tmp.drive",
    ".space/context.mdb", ".DS_Store", "vault_shadow", "backups", "checkpoints",
    "trash_archive", ".trash"
]

def scan_recent_modifications(hours: float = 12.0) -> Dict[str, List[Dict[str, Any]]]:
    """Сканирует недавно измененные файлы во всех ключевых пространствах."""
    now = time.time()
    cutoff = now - (hours * 3600)
    results = {
        "terminal": [],
        "pulsar": [],
        "and_os": [],
        "vault_projects": []
    }

    scan_targets = [
        (os.path.join(PULSAR_ROOT, "AND_Terminal"), "terminal"),
        (PULSAR_ROOT, "pulsar"),
        (AND_OS_ROOT, "and_os"),
        (VAULT_ROOT, "vault_projects")
    ]

    seen_paths = set()

    for base_dir, cat in scan_targets:
        if not os.path.exists(base_dir):
            continue
        for root, dirs, files in os.walk(base_dir):
            if any(ign in root for ign in IGNORE_SUBSTR):
                continue
            for f in files:
                full_p = os.path.join(root, f)
                if full_p in seen_paths:
                    continue
                if any(ign in f for ign in IGNORE_SUBSTR):
                    continue
                try:
                    mtime = os.path.getmtime(full_p)
                    if mtime >= cutoff:
                        seen_paths.add(full_p)
                        dt_min = round((now - mtime) / 60, 1)
                        rel_p = os.path.relpath(full_p, VAULT_ROOT if cat != "pulsar" else PULSAR_ROOT)
                        results[cat].append({
                            "file": os.path.basename(full_p),
                            "rel_path": rel_p,
                            "min_ago": dt_min,
                            "size_bytes": os.path.getsize(full_p)
                        })
                except OSError as e:
                    sys.stderr.write(f"[sync_preflight] Warning inspecting {full_p}: {e}\n")

    for k in results:
        results[k].sort(key=lambda x: x["min_ago"])
    return results

def sync_terminal_delta() -> List[str]:
    """Синхронизирует дельту Терминала между Pulsar и and_os/opt/terminal по mtime."""
    src = os.path.join(PULSAR_ROOT, "AND_Terminal")
    dst = os.path.join(AND_OS_ROOT, "opt/terminal")
    if not (os.path.exists(src) and os.path.exists(dst)):
        return []

    synced = []
    # Check Pulsar -> and_os
    for root, dirs, files in os.walk(src):
        if any(ign in root for ign in IGNORE_SUBSTR):
            continue
        for f in files:
            if any(ign in f for ign in IGNORE_SUBSTR):
                continue
            src_f = os.path.join(root, f)
            rel = os.path.relpath(src_f, src)
            dst_f = os.path.join(dst, rel)
            
            # If src newer than dst, update dst
            if not os.path.exists(dst_f) or os.path.getmtime(src_f) > os.path.getmtime(dst_f) + 1.0:
                os.makedirs(os.path.dirname(dst_f), exist_ok=True)
                shutil.copy2(src_f, dst_f)
                synced.append(f"Pulsar -> and_os: {rel}")
            # If dst newer than src (and not CONTEXT.md)
            elif rel != "CONTEXT.md" and os.path.getmtime(dst_f) > os.path.getmtime(src_f) + 1.0:
                os.makedirs(os.path.dirname(src_f), exist_ok=True)
                shutil.copy2(dst_f, src_f)
                synced.append(f"and_os -> Pulsar: {rel}")

    return synced

def generate_preflight_summary(hours: float = 12.0) -> Dict[str, Any]:
    """Генерирует лаконичную сводку состояния для агента."""
    synced = sync_terminal_delta()
    mods = scan_recent_modifications(hours)
    
    total_recent = sum(len(v) for v in mods.values())
    
    return {
        "status": "READY",
        "synced_terminal_files": synced,
        "recent_modifications_count": total_recent,
        "hot_files": {
            "terminal": [f["rel_path"] for f in mods["terminal"][:5]],
            "pulsar_apps": [f["rel_path"] for f in mods["pulsar"][:5]],
            "and_os_core": [f["rel_path"] for f in mods["and_os"][:5]],
            "vault": [f["rel_path"] for f in mods["vault_projects"][:5]]
        }
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Pre-flight delta scanner & synchronizer")
    parser.add_argument("--hours", type=float, default=12.0, help="Hours window (default: 12.0)")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--sync-only", action="store_true", help="Run sync only")
    args = parser.parse_args()

    if args.sync_only:
        synced = sync_terminal_delta()
        print(f"Synced {len(synced)} files.")
        for s in synced:
            print(f"  • {s}")
        return

    summary = generate_preflight_summary(args.hours)
    
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("=== 🛰️ PRE-FLIGHT DELTA & STRUCTURE SCAN (Rule №47) ===")
        if summary["synced_terminal_files"]:
            print(f"🔄 Синхронизировано файлов терминала: {len(summary['synced_terminal_files'])}")
            for s in summary["synced_terminal_files"]:
                print(f"   • {s}")
        else:
            print("🟢 Терминал синхронизирован: дельта между Pulsar и and_os/opt/terminal нулевая.")

        print(f"📊 Всего измененных файлов за {args.hours}ч: {summary['recent_modifications_count']}")
        for cat, flist in summary["hot_files"].items():
            if flist:
                print(f"  📁 {cat}: {', '.join(flist)}")
        
        # Rule №41: Scoped Rules Consistency Gate Check
        rule_issues = 0
        forbidden_patterns = ["rm -rf", "git push --force", "no tests", "ignore rules"]
        for root, dirs, files in os.walk(VAULT_ROOT):
            dirs[:] = [d for d in dirs if d not in [".git", "node_modules", ".archive", ".trash"]]
            for f in files:
                fl = f.lower()
                if fl in [".windsurfrules", ".cursorrules"] or ("rule" in fl and f.endswith(".md") and f != "rules.md"):
                    try:
                        with open(os.path.join(root, f), "r", encoding="utf-8") as rf:
                            c = rf.read().lower()
                        if any(p in c for p in forbidden_patterns):
                            rule_issues += 1
                    except OSError as e:
                        sys.stderr.write(f"[sync_preflight] Warning checking rules in {fp}: {e}\n")
        if rule_issues == 0:
            print("⚖️ Правила модулей и чатов согласованы с Глобальным Ядром (Правило №41: PASS).")
        else:
            print(f"⚠️ ВНИМАНИЕ: Найдено {rule_issues} коллизий в локальных правилах (Правило №41: WARN)!")

        # Rule №54: Holistic Component Binding Check (<5ms)
        skills_dir = os.path.join(AND_OS_ROOT, "lib/skills")
        routing_file = os.path.join(skills_dir, "ROUTING.md")
        if os.path.exists(routing_file) and os.path.exists(skills_dir):
            try:
                with open(routing_file, "r", encoding="utf-8") as rf:
                    rtxt = rf.read()
                active_skills = [d for d in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, d)) and not d.startswith(".") and d not in ["scripts", "references"]]
                orphans = [s for s in active_skills if s not in rtxt]
                if not orphans:
                    print(f"🔗 Связность компонентов: 100% (все {len(active_skills)} скиллов и модулей подключены к ядру, Правило №54: PASS).")
                else:
                    print(f"⚠️ ВНИМАНИЕ: Обнаружено {len(orphans)} изолированных скиллов: {orphans} (Правило №54: WARN)!")
            except (KeyError, TypeError, OSError) as e:
                sys.stderr.write(f"[sync_preflight] Warning inspecting orphans: {e}\n")
        print("==========================================================")

if __name__ == "__main__":
    main()
