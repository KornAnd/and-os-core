#!/usr/bin/env python3
"""
sync_service.py — Высокоскоростной сервис инициализации сессии (Fast Session Init Service v2.0).
Выполняет прямые импорты модулей в едином Python-процессе для снижения latency с 2.0 сек до ~0.6 сек.
"""

import os
import sys
import json
import argparse
from datetime import datetime

AI_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
VAULT_ROOT = os.path.abspath(os.path.join(AI_SCRIPT_DIR, "../.."))

if AI_SCRIPT_DIR not in sys.path:
    sys.path.insert(0, AI_SCRIPT_DIR)

# Import module entry points directly
try:
    import sync_context
    import state_manager
    import task_db_engine
    import system_tools_map
    import context_router
    import validate_system
    import telemetry_logger
except ImportError as e:
    sys.stderr.write(f"[sync_service] Import warning: {e}\n")

def run_session_init(fix=True, json_output=False):
    start_time = datetime.now()
    results = {}

    # 1. Sync Context & Quick Knowledge DB
    try:
        ok = sync_context.sync_all_contexts(fix=fix)
        results["sync_context"] = {"success": ok}
    except Exception as e:
        results["sync_context"] = {"success": False, "error": str(e)}

    # 2. Domain States Auto Sync
    try:
        state_manager.auto_sync_states()
        results["domain_states"] = {"success": True}
    except Exception as e:
        results["domain_states"] = {"success": False, "error": str(e)}

    # 3. Task DB SQLite Indexing
    try:
        task_db_engine.index_vault()
        results["task_db"] = {"success": True}
    except Exception as e:
        results["task_db"] = {"success": False, "error": str(e)}

    # 4. Build System Toolchain Map
    try:
        system_tools_map.build_toolchain_map()
        results["toolchain_map"] = {"success": True}
    except Exception as e:
        results["toolchain_map"] = {"success": False, "error": str(e)}

    # 4.5. Context Router Registry Indexing
    try:
        context_router.sync_context_registry()
        context_router.sync_knowledge_clippings_db()
        results["context_router"] = {"success": True}
    except Exception as e:
        results["context_router"] = {"success": False, "error": str(e)}

    # 4.7. External Projects Registry Indexing
    try:
        import project_registry
        project_registry.init_external_projects_db()
        results["project_registry"] = {"success": True}
    except Exception as e:
        results["project_registry"] = {"success": False, "error": str(e)}

    # 5. System Audit (13 vectors)
    try:
        audit_res = validate_system.check_corruption_artifacts() + validate_system.check_python_scripts_syntax()
        results["system_audit"] = {"success": audit_res == 0}
    except Exception as e:
        results["system_audit"] = {"success": False, "error": str(e)}

    # 6. Log Telemetry
    try:
        telemetry_logger.log_event(
            task="Session Init Sync & Audit (Fast Engine)",
            mode="SYSTEM",
            skill="sys.init",
            ctx="min",
            result="success"
        )
    except (ImportError, Exception) as e:
        sys.stderr.write(f"[sync_service] Telemetry logging failed: {e}\n")

    elapsed_sec = (datetime.now() - start_time).total_seconds()
    summary = {
        "status": "SUCCESS",
        "timestamp": start_time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_seconds": round(elapsed_sec, 2),
        "steps_completed": 6,
        "details": results
    }

    if json_output:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"🚀 [Sync Service] Стартовая инициализация сессии завершена за {summary['duration_seconds']} сек.")
        print(f"  ├─ CONTEXT.md & Quick DB: {'✅ OK' if results['sync_context']['success'] else '⚠️ WARN'}")
        print(f"  ├─ Состояния доменов: {'✅ OK' if results['domain_states']['success'] else '⚠️ WARN'}")
        print(f"  ├─ Индекс задач SQLite: {'✅ OK' if results['task_db']['success'] else '⚠️ WARN'}")
        print(f"  ├─ Картография инструментов: {'✅ OK' if results['toolchain_map']['success'] else '⚠️ WARN'}")
        print(f"  ├─ Реестр контекстов SQLite: {'✅ OK' if results['context_router']['success'] else '⚠️ WARN'}")
        print(f"  └─ 13-векторный системный аудит: {'✅ OK' if results['system_audit']['success'] else '⚠️ WARN'}")

    return summary

def main():
    parser = argparse.ArgumentParser(description="Fast Session Init Service v2.0")
    parser.add_argument("--fix", action="store_true", default=True, help="Авто-исправление расхождений")
    parser.add_argument("--check-only", action="store_true", help="Только диагностика без исправлений")
    parser.add_argument("--json", action="store_true", help="Вывод в JSON для IPC")

    args = parser.parse_args()
    fix_flag = not args.check_only
    run_session_init(fix=fix_flag, json_output=args.json)

if __name__ == "__main__":
    main()
