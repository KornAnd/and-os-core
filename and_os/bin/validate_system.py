#!/usr/bin/env python3
"""
validate_system.py — Модульный мастер-диспетчер самодиагностики и аудита AnD os.
Архитектура Health Grid (Ring 0 - Ring 4):
  - Ring 0: FSSyntaxProbe (ФС, байт-код, синтаксис, семантика путей)
  - Ring 1: GraphProbe (Граф знаний, 0% сирот, межостровные магистрали)
  - Ring 2: ContractProbe (AST контракты CLI, непротиворечивость правил, IPC схемы)
  - Ring 3: ManifestProbe (Манифесты ядра, безопасность, Air-Gap, DEV_PROTOCOL)
  - Ring 3.5: SkillProbe (Параллельный SOS аудит 50 скиллов)
  - Ring 4: RuntimeProbe (Живой рантайм, LaunchAgents порты, дисковый предохранитель)
"""

import os
import sys
import json
import shutil
import argparse
import time
from concurrent.futures import ThreadPoolExecutor

# Keep read-only audits from creating __pycache__ files, including in child probes.
sys.dont_write_bytecode = True
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
if VAULT_ROOT not in sys.path:
    sys.path.insert(0, VAULT_ROOT)
LIB_DIR = os.path.join(SCRIPT_DIR, "..", "lib")
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

from and_os.lib.health_grid.fs_syntax_probe import FSSyntaxProbe
from and_os.lib.health_grid.graph_probe import GraphProbe
from and_os.lib.health_grid.contract_probe import ContractProbe
from and_os.lib.health_grid.manifest_probe import ManifestProbe
from and_os.lib.health_grid.skill_probe import SkillProbe
from and_os.lib.health_grid.runtime_probe import RuntimeProbe
from and_os.lib.health_grid.clean_code_probe import CleanCodeProbe
from and_os.lib.health_grid.dod_probe import DoDProbe


def run_full_grid_audit(
    vault_root: str, fix: bool = False, verbose: bool = True, save_report: bool = False
) -> dict:
    t0 = time.time()

    probes = [
        ("fs_syntax", FSSyntaxProbe),
        ("graph", GraphProbe),
        ("contract", ContractProbe),
        ("clean_code", CleanCodeProbe),
        ("manifest", ManifestProbe),
        ("skill", SkillProbe),
        ("runtime", RuntimeProbe),
        ("dod_gate", DoDProbe),
    ]

    results = {}
    probe_failures = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_map = {

            executor.submit(probe_cls.run, vault_root, fix=fix, verbose=verbose): name
            for name, probe_cls in probes
        }
        for future, name in future_map.items():
            try:
                results[name] = future.result()
            except Exception as e:
                probe_failures[name] = f"{type(e).__name__}: {e}"
                print(f"[!] Ошибка исполнения зонда {name}: {probe_failures[name]}", file=sys.stderr)

    expected_probes = {name for name, _ in probes}
    missing_probes = sorted(expected_probes - set(results) - set(probe_failures))
    if missing_probes:
        for name in missing_probes:
            probe_failures[name] = "Probe did not return a result"

    total_issues = sum(max(0, int(r.issues_count)) for r in results.values())
    status_only_failures = sum(
        1 for r in results.values() if not r.passed and r.issues_count == 0
    )
    probes_passed = (
        set(results) == expected_probes
        and not probe_failures
        and all(r.passed and r.issues_count == 0 for r in results.values())
    )
    elapsed = round(time.time() - t0, 2)
    free_gb = round(shutil.disk_usage(vault_root).free / (1024 ** 3), 1)

    from and_os.lib.core.root_config import get_system_version
    sys_ver = get_system_version(vault_root)

    payload = {
        "status": "PASS" if probes_passed else ("FAIL" if probe_failures else "WARN"),
        "version": sys_ver,
        "elapsed_seconds": elapsed,
        "expected_probe_count": len(probes),
        "disk_free_gb": free_gb,
        "total_issues": total_issues + status_only_failures + len(probe_failures),
        "probe_failures": probe_failures,
        "probes": {k: v.to_dict() for k, v in results.items()},
        "report_persistence": "not_requested"
    }

    if save_report:
        health_cache = os.path.join(vault_root, "and_os", "var", "system_health.json")
        try:
            os.makedirs(os.path.dirname(health_cache), exist_ok=True)
            payload["report_persistence"] = "saved"
            with open(health_cache, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except OSError as e:
            payload["report_persistence"] = "failed"
            payload["report_persistence_error"] = f"{type(e).__name__}: {e}"

    return payload


def main():
    parser = argparse.ArgumentParser(description="AnD os v8.1 Health Grid System Auditor")
    parser.add_argument("--check", action="store_true", help="Развернутый аудит системы")
    parser.add_argument("--fix", action="store_true", help="Автоматическое устранение найденных дефектов")
    parser.add_argument("--compact", "-c", action="store_true", help="Токеноэффективная экспресс-сводка (1 строка)")
    parser.add_argument("--json", action="store_true", help="Вывод в формате JSON")
    parser.add_argument("--save-report", action="store_true", help="Явно сохранить срез в and_os/var/system_health.json")
    parser.add_argument("--deep", action="store_true", help="Глубокая развернутая проверка")
    args = parser.parse_args()

    verbose = not (args.compact or args.json)

    if verbose:
        try:
            from and_os.lib.core.root_config import get_system_version
            ver_str = f"v{get_system_version()}"
        except Exception:
            ver_str = "v8.1.0"
        mode_str = "ИСПРАВЛЕНИЕ (--fix)" if args.fix else "ДИАГНОСТИКА (Health Grid)"
        print(f"\nЗапуск Health Grid валидации AnD os ({ver_str}): режим {mode_str}\n" + "=" * 65)

    report = run_full_grid_audit(
        VAULT_ROOT, fix=args.fix, verbose=verbose, save_report=args.save_report
    )
    all_passed = report["status"] == "PASS" and report["report_persistence"] != "failed"

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if all_passed else 1

    if args.compact:
        if report["report_persistence"] == "failed":
            tag = "🔴 [AUDIT REPORT: SAVE FAILED]"
        elif report["status"] == "PASS":
            tag = "🟢 [AUDIT L1: PASS]"
        elif report["status"] == "FAIL":
            tag = f"🔴 [AUDIT L1: FAIL ({report['total_issues']} issues)]"
        else:
            tag = f"🟡 [AUDIT L1: WARN ({report['total_issues']} issues)]"
        expected = report["expected_probe_count"]
        completed = len(report["probes"])
        passed = sum(
            1 for pdata in report["probes"].values()
            if pdata["passed"] and pdata["issues_count"] == 0
        )
        failed = len(report.get("probe_failures", {}))
        print(
            f"{tag} Зонды: PASS {passed}/{expected}; завершено {completed}/{expected}; "
            f"ошибок запуска {failed}; проблем {report['total_issues']}; "
            f"время {report['elapsed_seconds']}с; свободно {report['disk_free_gb']} ГБ; "
            f"срез: {report['report_persistence']}"
        )
        return 0 if all_passed else 1

    # Подробный человекочитаемый вывод
    for probe_name, pdata in report["probes"].items():
        st_icon = "🟢" if pdata["passed"] else "🔴"
        print(f"{st_icon} {pdata['name']}: {'OK' if pdata['passed'] else 'ДЕФЕКТЫ'}")
        if pdata["errors"]:
            for err in pdata["errors"]:
                print(f"    - [ERROR] {err}")
        if pdata["warnings"]:
            for w in pdata["warnings"]:
                print(f"    - [WARN] {w}")

    for probe_name, error in report.get("probe_failures", {}).items():
        print(f"🔴 Зонд {probe_name} не завершился: {error}")
    if report["report_persistence"] == "failed":
        print(f"🔴 Не удалось сохранить срез аудита: {report['report_persistence_error']}")

    print("\n" + "=" * 65)
    if report["report_persistence"] == "failed":
        print("ИТОГ: Проверка здоровья завершена, но сохранение отчета завершилось ошибкой.")
        return 1
    if report["status"] == "PASS":
        print(f"ИТОГ: Все обязательные зонды пройдены за {report['elapsed_seconds']}с.")
        return 0
    if report["status"] == "FAIL":
        print(f"ИТОГ: Аудит не завершен; зондов с ошибкой: {len(report.get('probe_failures', {}))}.")
        return 1
    print(f"ИТОГ: Обнаружено потенциальных дефектов: {report['total_issues']}.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
