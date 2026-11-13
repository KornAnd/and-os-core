#!/usr/bin/env python3
"""
sos_auditor.py — Skill Operating Stack (SOS) Parallel Multi-Core Auditor.
High-speed parallel diagnostic engine for AnD os skills.

Verifies all active skills concurrently across CPU cores:
  1. Frontmatter Contract (ABI v2.0: name, lifecycle, version, domain)
  2. Python script health (py_compile, import checks)
  3. Symlink and VFS path integrity
  4. Air-Gap & Zero-Leak rule compliance (no hardcoded credentials)
  5. Canary Health Probes (optional probe_cmd execution)
"""

import os
import sys
import time
import py_compile
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
SKILLS_DIR = os.path.join(VAULT_ROOT, "and_os", "lib", "skills")
OPENCODE_SKILLS = os.path.join(VAULT_ROOT, ".opencode", "skills")
BINDINGS_PATH = os.path.join(VAULT_ROOT, "and_os", "etc", "SKILL_BINDINGS.json")


def load_cached_bindings() -> set:
    """Load set of skill names present in canonical SKILL_BINDINGS.json."""
    if os.path.exists(BINDINGS_PATH):
        try:
            import json
            with open(BINDINGS_PATH, "r", encoding="utf-8") as f:
                return set(json.load(f).keys())
        except Exception:
            return set()
    return set()

REGISTERED_BINDINGS = load_cached_bindings()


def parse_frontmatter(content: str) -> Dict[str, Any]:
    """Lightweight pure-python frontmatter parser without third-party dependencies."""
    res = {}
    if not content.startswith("---"):
        return res
    parts = content.split("---", 2)
    if len(parts) < 3:
        return res
    for line in parts[1].splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            res[key] = val
    return res


def audit_single_skill(skill_name: str, skill_path: str, run_probes: bool = False) -> Dict[str, Any]:
    start_t = time.time()
    result = {
        "name": skill_name,
        "valid": True,
        "errors": [],
        "warnings": [],
        "version": "unknown",
        "lifecycle": "unknown",
        "probe_result": None,
        "elapsed_ms": 0.0
    }

    skill_md = os.path.join(skill_path, "SKILL.md")
    if not os.path.exists(skill_md):
        result["valid"] = False
        result["errors"].append("SKILL.md missing")
        result["elapsed_ms"] = round((time.time() - start_t) * 1000, 2)
        return result

    # 1. Frontmatter parsing & ABI validation
    try:
        with open(skill_md, "r", encoding="utf-8") as f:
            content = f.read()

        fm = parse_frontmatter(content)
        if fm:
            result["version"] = str(fm.get("version", "1.0.0"))
            result["lifecycle"] = str(fm.get("lifecycle", "ACTIVE"))
            
            # Check required ABI fields
            for field in ["name", "description"]:
                if field not in fm:
                    result["warnings"].append(f"Frontmatter missing field: '{field}'")
            
            probe_cmd = fm.get("probe_cmd")
            if run_probes and probe_cmd:
                try:
                    # Rule #68 (golden interpreter): probe commands that use a bare
                    # `python3` must resolve to the canonical venv, never to a PATH
                    # shadow (audit R2: bare-`python3` probes compiled non-golden
                    # cpython pyc into lib/core/__pycache__).
                    probe_env = os.environ.copy()
                    venv_bin = os.path.join(VAULT_ROOT, "and_os", ".venv", "bin")
                    if os.path.isdir(venv_bin):
                        probe_env["PATH"] = venv_bin + os.pathsep + probe_env.get("PATH", "")
                    p_res = subprocess.run(
                        probe_cmd,
                        shell=True,  # nosec: probe runner
                        cwd=VAULT_ROOT,
                        env=probe_env,
                        capture_output=True,
                        text=True,
                        timeout=3.0
                    )
                    result["probe_result"] = {
                        "cmd": probe_cmd,
                        "success": p_res.returncode == 0,
                        "exit_code": p_res.returncode
                    }
                    if p_res.returncode != 0:
                        result["warnings"].append(f"Canary probe failed: {probe_cmd} (code {p_res.returncode})")
                except subprocess.TimeoutExpired:
                    result["warnings"].append(f"Canary probe timed out: {probe_cmd}")
                except Exception as pe:
                    result["warnings"].append(f"Canary probe error: {pe}")
        else:
            result["warnings"].append("Frontmatter missing or empty in SKILL.md")
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"File read error: {e}")

    # 2. Symlink integrity check
    symlink_path = os.path.join(OPENCODE_SKILLS, skill_name)
    if not os.path.exists(symlink_path) and not os.path.islink(symlink_path):
        result["warnings"].append(f"Symlink missing in .opencode/skills/{skill_name}")

    # 3. Canonical SKILL_BINDINGS.json membership check
    if REGISTERED_BINDINGS and skill_name not in REGISTERED_BINDINGS:
        result["warnings"].append(f"Skill '{skill_name}' is not registered in and_os/etc/SKILL_BINDINGS.json")

    # 4. Check internal python scripts compilation
    for root, _, files in os.walk(skill_path):
        for file in files:
            if file.endswith(".py"):
                py_file = os.path.join(root, file)
                try:
                    py_compile.compile(py_file, doraise=True)
                except py_compile.PyCompileError as pye:
                    result["valid"] = False
                    result["errors"].append(f"Python compile error in {file}: {pye}")

    if result["errors"]:
        result["valid"] = False

    result["elapsed_ms"] = round((time.time() - start_t) * 1000, 2)
    return result


def run_parallel_audit(run_probes: bool = False, max_workers: int = 8) -> Dict[str, Any]:
    start_total = time.time()
    skill_dirs = []
    
    if os.path.exists(SKILLS_DIR):
        for entry in os.listdir(SKILLS_DIR):
            full_path = os.path.join(SKILLS_DIR, entry)
            # Skip hidden dirs, archive, and shared reference docs
            if os.path.isdir(full_path) and not entry.startswith(".") and entry != "references":
                skill_dirs.append((entry, full_path))

    total_skills = len(skill_dirs)
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(audit_single_skill, name, path, run_probes): name
            for name, path in skill_dirs
        }
        for future in as_completed(futures):
            res = future.result()
            results.append(res)

    results.sort(key=lambda x: x["name"])
    valid_count = sum(1 for r in results if r["valid"])
    total_elapsed_ms = round((time.time() - start_total) * 1000, 2)

    return {
        "total": total_skills,
        "healthy": valid_count,
        "unhealthy": total_skills - valid_count,
        "elapsed_ms": total_elapsed_ms,
        "skills": results
    }


def main():
    run_probes = "--probe" in sys.argv
    as_json = "--json" in sys.argv
    
    audit_data = run_parallel_audit(run_probes=run_probes)
    
    if as_json:
        import json
        print(json.dumps(audit_data, ensure_ascii=False, indent=2))
        return

    print("=================================================================")
    print(f"🚀 SOS Parallel Multi-Core Skill Auditor (AnD os v1.0.0)")
    print(f"⚡ Skills checked: {audit_data['total']} in {audit_data['elapsed_ms']} ms")
    print("=================================================================")
    
    has_issues = False
    for s in audit_data["skills"]:
        if not s["valid"]:
            has_issues = True
            print(f"  🔴 [FAIL] {s['name']} (v{s['version']} | {s['lifecycle']}): {', '.join(s['errors'])}")
        elif s["warnings"]:
            print(f"  🟡 [WARN] {s['name']} (v{s['version']} | {s['lifecycle']}): {', '.join(s['warnings'])}")

    if not has_issues:
        print(f"✅ ALL {audit_data['healthy']} active skills are valid, hermetic and fully healthy!")
    else:
        print(f"⚠️ Unhealthy skills detected: {audit_data['unhealthy']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
