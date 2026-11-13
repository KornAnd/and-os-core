#!/usr/bin/env python3
"""
validate_system.py — Modular master dispatcher of the self-diagnostics and audit of AnD os.
Health Grid architecture (Ring 0 - Ring 4):
  - Ring 0: FSSyntaxProbe (FS, bytecode, syntax, path semantics)
  - Ring 1: GraphProbe (knowledge graph, 0% orphans, cross-island highways)
  - Ring 2: ContractProbe (CLI AST contracts, rule consistency, IPC schemas)
  - Ring 3: ManifestProbe (kernel manifests, security, Air-Gap, DEV_PROTOCOL)
  - Ring 3.5: SkillProbe (parallel SOS audit of the 50 skills)
  - Ring 4: RuntimeProbe (live runtime, LaunchAgents ports, disk fuse)
"""

import os
import sys
import json
import shutil
import argparse
import time
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict

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

DEFAULT_POLICY = {"blocking": True, "timeout_sec": 120}


def load_probe_policy(vault_root: str, probe_names) -> Dict[str, Dict[str, Any]]:
    """Loads and_os/etc/probe_policy.json (audit R3, F4): the declarative
    blocking/advisory + per-probe timeout contract of the Health Grid.
    A missing or corrupt policy degrades to all-blocking 120s defaults."""
    policy_path = os.path.join(vault_root, "and_os", "etc", "probe_policy.json")
    try:
        with open(policy_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        base = {**DEFAULT_POLICY, **data.get("default", {})}
        declared = data.get("probes", {})
        return {name: {**base, **declared.get(name, {})} for name in probe_names}
    except (OSError, ValueError) as err:
        sys.stderr.write(f"[validate_system] Notice: probe policy unavailable ({err}); "
                         f"defaults applied (blocking, {DEFAULT_POLICY['timeout_sec']}s)\n")
        return {name: dict(DEFAULT_POLICY) for name in probe_names}


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
    probe_timeouts = {}
    policy = load_probe_policy(vault_root, [name for name, _ in probes])
    executor = ThreadPoolExecutor(max_workers=8)
    future_map = {
        executor.submit(probe_cls.run, vault_root, fix=fix, verbose=verbose): name
        for name, probe_cls in probes
    }
    try:
        for future, name in future_map.items():
            timeout = int(policy.get(name, DEFAULT_POLICY).get("timeout_sec", DEFAULT_POLICY["timeout_sec"]))
            try:
                results[name] = future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                # A probe thread cannot be killed in-process; the audit
                # records the failure, prints the report and force-exits.
                probe_timeouts[name] = timeout
                probe_failures[name] = f"probe timeout after {timeout}s (hung probe)"
                print(f"[!] Probe {name} timed out after {timeout}s", file=sys.stderr)
            except Exception as e:
                probe_failures[name] = f"{type(e).__name__}: {e}"
                print(f"[!] Probe execution error {name}: {probe_failures[name]}", file=sys.stderr)
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

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
        "probe_timeouts": probe_timeouts,
        "probe_policy": policy,
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


def _force_exit_on_timeouts(report: dict) -> None:
    """A hung probe thread cannot be killed in-process (Python threads are
    not killable). Once the report is fully printed, the audit force-exits
    via os._exit(1) so a hung thread cannot keep the process alive
    (R3-CON-1 / F4(e); the report is printed BEFORE this call)."""
    timeouts = report.get("probe_timeouts") or {}
    if timeouts:
        names = ", ".join(f"{name} (> {timeout}s)" for name, timeout in sorted(timeouts.items()))
        sys.stderr.write(f"[!] Force-exit: hung probe(s): {names}; leaving via os._exit(1).\n")
        os._exit(1)


def main():
    parser = argparse.ArgumentParser(description="AnD os v1.0.0 Health Grid System Auditor")
    parser.add_argument("--fix", action="store_true", help="Automatic elimination of the found defects")
    parser.add_argument("--compact", "-c", action="store_true", help="Token-efficient express summary (1 line)")
    parser.add_argument("--json", action="store_true", help="JSON format output")
    parser.add_argument("--save-report", action="store_true", help="Explicitly save the snapshot to and_os/var/system_health.json")
    args = parser.parse_args()

    verbose = not (args.compact or args.json)

    if verbose:
        try:
            from and_os.lib.core.root_config import get_system_version
            ver_str = f"v{get_system_version()}"
        except Exception:
            ver_str = "v1.0.0"
        mode_str = "REPAIR (--fix)" if args.fix else "DIAGNOSTICS (Health Grid)"
        print(f"\nLaunching the Health Grid validation of AnD os ({ver_str}): mode {mode_str}\n" + "=" * 65)

    report = run_full_grid_audit(
        VAULT_ROOT, fix=args.fix, verbose=verbose, save_report=args.save_report
    )
    all_passed = report["status"] == "PASS" and report["report_persistence"] != "failed"

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        _force_exit_on_timeouts(report)
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
            f"{tag} Probes: PASS {passed}/{expected}; completed {completed}/{expected}; "
            f"launch errors {failed}; issues {report['total_issues']}; "
            f"time {report['elapsed_seconds']}s; free {report['disk_free_gb']} GB; "
            f"snapshot: {report['report_persistence']}"
        )
        _force_exit_on_timeouts(report)
        return 0 if all_passed else 1

    # Detailed human-readable output
    for probe_name, pdata in report["probes"].items():
        st_icon = "🟢" if pdata["passed"] else "🔴"
        print(f"{st_icon} {pdata['name']}: {'OK' if pdata['passed'] else 'DEFECTS'}")
        if pdata["errors"]:
            for err in pdata["errors"]:
                print(f"    - [ERROR] {err}")
        if pdata["warnings"]:
            for w in pdata["warnings"]:
                print(f"    - [WARN] {w}")

    for probe_name, error in report.get("probe_failures", {}).items():
        print(f"🔴 Probe {probe_name} did not finish: {error}")
    if report["report_persistence"] == "failed":
        print(f"🔴 Failed to save the audit snapshot: {report['report_persistence_error']}")

    print("\n" + "=" * 65)
    if report["report_persistence"] == "failed":
        print("RESULT: the health check finished, but the report save ended with an error.")
        exit_code = 1
    elif report["status"] == "PASS":
        print(f"RESULT: all mandatory probes passed in {report['elapsed_seconds']}s.")
        exit_code = 0
    elif report["status"] == "FAIL":
        print(f"RESULT: the audit did not finish; probes with errors: {len(report.get('probe_failures', {}))}.")
        exit_code = 1
    else:
        print(f"RESULT: potential defects detected: {report['total_issues']}.")
        exit_code = 1
    _force_exit_on_timeouts(report)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
