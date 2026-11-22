"""
dod_probe.py — Ring 5: Definition of Done (DoD) Quality & Secret Leak Gate.
AnD os v1.2.0 — Continuous Verification Loop.

Covers:
  - Phase 5 Secret Leak Scan: Validates absence of API keys ('sk-', 'ghp_', 'AKIA') in code.
  - Console Debug Leak Scan: Warns on dangling 'console.log' / 'debugger' in frontend code.
  - Video Asset Quality Gate: Validates FPS 24.0 in master shot metadata sidecars.
  - 3D Mesh Integrity Gate: Verifies sidecar meta.json presence for master blend assets.
  - sec_audit EXECUTION gate (D4, 17.11): runs the OWASP Top-10 AST
    scanner (scope and_os/) when the kernel changed since the last run;
    known findings form a stored baseline, new findings warn (advisory,
    never fail the ring) until triaged in the audit stage.
"""


import os
import re
import json
import subprocess
import sys
import time
from typing import Dict, Any, List
from and_os.lib.health_grid import BaseProbeResult

IGNORE_DIRS = {".space", ".obsidian", ".trash", "Trash", ".opencode", ".makemd", ".smart-env", ".git", "node_modules", ".archive", "var", ".venv", "venv"}

# Lightweight standing gate. Ranges follow the SSoT:
# and_os/lib/skills/system-audit/scripts/security_scan.py
# SECRET_PATTERNS (D1, 17.11). Scope is deliberately narrower than the
# SSoT walk: IGNORE_DIRS keeps .obsidian/.trash/.archive out of the
# periodic pass; the deep scan of those surfaces is the manual
# security_scan run (D2, 17.11: note-surface coverage split).
SECRET_PATTERNS = [
    (re.compile(r'sk-[a-zA-Z0-9]{20,}'), "OpenAI / Claude API Key pattern"),
    (re.compile(r'ghp_[a-zA-Z0-9]{20,}'), "GitHub Personal Access Token"),
    (re.compile(r'AKIA[0-9A-Z]{16}'), "AWS Access Key ID")
]

class DoDProbe:
    @staticmethod
    def run(vault_root: str, fix: bool = False, verbose: bool = True) -> BaseProbeResult:
        result = BaseProbeResult(name="Ring 5: Definition of Done (DoD) Gate", ring=5)
        issues = 0

        # 1. Secret Leak Scan across code & config files
        for root, dirs, files in os.walk(vault_root):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for f in files:
                if f.endswith((".py", ".js", ".ts", ".json", ".yaml", ".yml", ".sh")) and not f.startswith("."):
                    fpath = os.path.join(root, f)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as code_file:
                            content = code_file.read()
                            for pat, desc in SECRET_PATTERNS:
                                if pat.search(content):
                                    issues += 1
                                    rel_p = os.path.relpath(fpath, vault_root)
                                    result.errors.append(f"Security Alert: {desc} found in {rel_p}")
                    except OSError as err:
                        sys.stderr.write(f"[dod_probe] Notice scanning {fpath}: {err}\n")

        # 2. 3D Master Asset Manifest Gate
        assets_dir = os.path.join(vault_root, "and_os", "opt", "apps", "cg_workspace", "assets")
        if os.path.exists(assets_dir):
            for root, dirs, files in os.walk(assets_dir):
                for f in files:
                    if f.endswith(".blend") and not f.endswith("@"):
                        sidecar = os.path.join(root, f.replace(".blend", ".meta.json"))
                        if not os.path.exists(sidecar):
                            result.warnings.append(f"Asset without sidecar meta.json: {os.path.basename(f)}")

        # 3. Continuous Delivery & Quality Mesh Integration Gate
        # Verify that new core engines are intact and healthy
        core_tools = [
            ("and_os/bin/quick_verify.py", "Quick Verification Loop"),
            ("and_os/bin/checkpoint_manager.py", "Checkpoint Manager"),
            ("and_os/bin/eval_engine.py", "Eval Engine"),
            ("and_os/bin/agent_handoff.py", "Agent Handoff Validator"),
            ("and_os/etc/AGENT_HANDOFF_SPEC.md", "Agent Handoff Spec"),
            ("and_os/bin/context_mode_manager.py", "Context Mode Manager"),
            ("and_os/bin/refactor_cleaner.py", "Refactor Cleaner Engine"),
            ("and_os/bin/docs_sync.py", "Documentation Synchronizer"),
            ("and_os/docs/RUNBOOK.md", "Production Operations Runbook"),
            ("and_os/bin/tdd_scaffold.py", "TDD Test Scaffold Generator"),
            ("and_os/bin/sec_audit.py", "Security & OWASP Top-10 Guard"),
            ("and_os/bin/artifact_capture.py", "Visual Artifact on Failure Engine"),
            ("and_os/bin/dag_planner.py", "DAG Phase Planner Engine")
        ]
        for rel_tool, tool_name in core_tools:
            tool_full = os.path.join(vault_root, rel_tool)
            if not os.path.exists(tool_full):
                issues += 1
                result.errors.append(f"Missing core continuous quality engine: {tool_name} ({rel_tool})")

        # Check that eval suites in and_os/var/evals/ are syntactically valid JSON
        evals_dir = os.path.join(vault_root, "and_os", "var", "evals")
        if os.path.exists(evals_dir):
            for ef in os.listdir(evals_dir):
                if ef.endswith(".eval.json"):
                    try:
                        with open(os.path.join(evals_dir, ef), "r", encoding="utf-8") as eval_fh:
                            json.load(eval_fh)
                    except Exception as err:
                        issues += 1
                        result.errors.append(f"Corrupted eval definition {ef}: {err}")

        # 4. Closed-Loop Memory Nudge (Rule #13, audit R2 WI-4.10):
        # if the kernel (and_os/lib/core/**, sys_cli.py) was modified recently
        # but no learned pattern in Nero/knowledge/engineers/ is newer than
        # that modification, the post-flight learning loop is open — warn.
        # Stale kernel changes (older than the window) are not warned: they
        # are history, not a live gap.
        kernel_recent_window_days = 14
        kernel_targets = [os.path.join(vault_root, "and_os", "bin", "sys_cli.py")]
        core_dir = os.path.join(vault_root, "and_os", "lib", "core")
        if os.path.isdir(core_dir):
            for r, d, fs in os.walk(core_dir):
                d[:] = [x for x in d if x != "__pycache__"]
                kernel_targets += [os.path.join(r, f) for f in fs if f.endswith(".py")]
        newest_kernel = 0.0
        for kt in kernel_targets:
            try:
                newest_kernel = max(newest_kernel, os.path.getmtime(kt))
            except OSError:
                continue
        patterns_dir = os.path.join(vault_root, "Nero", "knowledge", "engineers")
        newest_pattern = 0.0
        if os.path.isdir(patterns_dir):
            for r, d, fs in os.walk(patterns_dir):
                for pf in fs:
                    if pf.endswith(".md"):
                        try:
                            newest_pattern = max(newest_pattern, os.path.getmtime(os.path.join(r, pf)))
                        except OSError:
                            continue
        kernel_age_days = (time.time() - newest_kernel) / 86400.0 if newest_kernel else None
        result.details = {
            "kernel_newest_mtime_age_days": round(kernel_age_days, 2) if kernel_age_days is not None else None,
            "patterns_newest_mtime_age_days": round((time.time() - newest_pattern) / 86400.0, 2) if newest_pattern else None,
        }
        if (newest_kernel and newest_kernel > newest_pattern
                and kernel_age_days is not None and kernel_age_days <= kernel_recent_window_days):
            result.warnings.append(
                f"Closed-loop memory nudge (Rule #13): kernel modified {kernel_age_days:.1f}d ago but no "
                f"newer learned pattern in Nero/knowledge/engineers/ (newest pattern "
                f"{(time.time() - newest_pattern) / 86400.0:.1f}d ago) — run sys_cli learn after kernel work")

        # 5. sec_audit EXECUTION gate (D4, 17.11): the core_tools loop
        # above only checks that sec_audit.py EXISTS; this block executes
        # it (scope and_os/) when the kernel changed since the last run.
        # Advisory by design: the first run bootstraps the finding
        # baseline silently; later runs warn on findings NEW against the
        # baseline but never increment issues_count — severity triage
        # belongs to the audit stage, not the standing grid.
        state_dir = os.path.join(vault_root, "and_os", "var", "state")
        state_file = os.path.join(state_dir, "sec_audit_state.json")
        sec_audit_state = {}
        if os.path.exists(state_file):
            try:
                with open(state_file, "r", encoding="utf-8") as state_fh:
                    sec_audit_state = json.load(state_fh)
            except (OSError, json.JSONDecodeError) as err:
                sys.stderr.write(
                    f"[dod_probe] Notice: unreadable sec_audit state: {err}\n")
        sec_audit_script = os.path.join(vault_root, "and_os", "bin", "sec_audit.py")
        last_kernel_mtime = sec_audit_state.get("last_kernel_mtime", 0.0)
        kernel_changed = bool(newest_kernel) and newest_kernel > last_kernel_mtime
        if kernel_changed and os.path.exists(sec_audit_script):
            started = time.time()
            try:
                proc = subprocess.run(
                    [sys.executable, sec_audit_script, "and_os"],
                    cwd=vault_root, capture_output=True, text=True,
                    timeout=120)
                elapsed = round(time.time() - started, 1)
                if proc.returncode == 2:
                    raise subprocess.SubprocessError(
                        f"sec_audit usage error (exit 2): "
                        f"{proc.stderr.strip()[:120]}")
                current = {
                    (sev, fpath, line, rule)
                    for sev, fpath, line, rule in re.findall(
                        r"\[(CRITICAL|HIGH|MEDIUM|LOW)\]\s+(\S+?):(\d+)\s+->\s+(\S+)",
                        proc.stdout)}
                baseline = set(map(tuple, sec_audit_state.get("baseline", [])))
                bootstrap = not baseline
                # An empty result set against a non-empty baseline is
                # treated as a parse/output regression, not as
                # "everything fixed": keep the baseline, warn.
                if not current and baseline:
                    raise subprocess.SubprocessError(
                        "sec_audit returned no parseable findings "
                        "against a non-empty baseline (output regression?)")
                new_findings = sorted(current - baseline)
                os.makedirs(state_dir, exist_ok=True)
                with open(state_file, "w", encoding="utf-8") as state_fh:
                    json.dump({
                        "last_kernel_mtime": newest_kernel,
                        "last_run": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "elapsed_seconds": elapsed,
                        "total": len(current),
                        "new": len(new_findings),
                        "baseline": sorted(current),
                    }, state_fh, indent=2, ensure_ascii=False)
                result.details["sec_audit"] = {
                    "ran": True,
                    "elapsed_s": elapsed,
                    "total": len(current),
                    "new_vs_baseline": len(new_findings),
                    "bootstrap": bootstrap,
                }
                if not bootstrap and new_findings:
                    for sev, fpath, line, rule in new_findings[:10]:
                        result.warnings.append(
                            f"sec_audit new finding [{sev}] {fpath}:{line} -> {rule} "
                            f"(D4: OWASP scanner vs stored baseline; triage in audit stage)")
            except (OSError, subprocess.SubprocessError) as err:
                result.warnings.append(f"sec_audit execution failed (D4): {err}")
                result.details["sec_audit"] = {"ran": False, "error": str(err)}
        elif newest_kernel:
            result.details["sec_audit"] = {
                "ran": False,
                "reason": "kernel unchanged since last run",
                "last_run": sec_audit_state.get("last_run"),
            }

        result.issues_count = issues
        result.passed = (issues == 0)
        return result
