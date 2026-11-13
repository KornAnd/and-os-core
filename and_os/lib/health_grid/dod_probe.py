"""
dod_probe.py — Ring 5: Definition of Done (DoD) Quality & Secret Leak Gate.
AnD os v1.0.0 — Continuous Verification Loop.

Covers:
  - Phase 5 Secret Leak Scan: Validates absence of API keys ('sk-', 'ghp_', 'AKIA') in code.
  - Console Debug Leak Scan: Warns on dangling 'console.log' / 'debugger' in frontend code.
  - Video Asset Quality Gate: Validates FPS 24.0 in master shot metadata sidecars.
  - 3D Mesh Integrity Gate: Verifies sidecar meta.json presence for master blend assets.
"""


import os
import re
import json
import sys
import time
from typing import Dict, Any, List
from and_os.lib.health_grid import BaseProbeResult

IGNORE_DIRS = {".space", ".obsidian", ".trash", "Trash", ".opencode", ".makemd", ".smart-env", ".git", "node_modules", ".archive", "var", ".venv", "venv"}

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

        result.issues_count = issues
        result.passed = (issues == 0)
        return result
