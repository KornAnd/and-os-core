"""
skill_probe.py — Ring 3.5: Multi-core Parallel Skill Operating Stack (SOS) Probe.
Covers:
  - Skill ABI verification (name, version, lifecycle, domain)
  - Symlinks in .opencode/skills/
  - Internal skill script compilation
  - Optional canary test execution (probe_cmd)
"""

import os
import sys
import time
import tokenize
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List
from and_os.lib.health_grid import BaseProbeResult

IGNORE_DIRS = {".space", ".obsidian", ".trash", "Trash", ".opencode", ".makemd", ".smart-env", ".git", "node_modules", ".archive", "scripts", "references"}


def parse_frontmatter(content: str) -> Dict[str, Any]:
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
            res[key.strip()] = val.strip().strip('"').strip("'")
    return res


class SkillProbe:
    @staticmethod
    def audit_single_skill(vault_root: str, skill_name: str, skill_path: str, run_probes: bool = False) -> Dict[str, Any]:
        result = {
            "name": skill_name,
            "valid": True,
            "errors": [],
            "warnings": [],
            "version": "unknown",
            "lifecycle": "unknown",
            "probe_result": None
        }

        skill_md = os.path.join(skill_path, "SKILL.md")
        if not os.path.exists(skill_md):
            result["valid"] = False
            result["errors"].append("SKILL.md missing")
            return result

        # 1. Frontmatter
        try:
            with open(skill_md, "r", encoding="utf-8") as f:
                content = f.read()
            fm = parse_frontmatter(content)
            if fm:
                result["version"] = str(fm.get("version", "1.0.0"))
                result["lifecycle"] = str(fm.get("lifecycle", "ACTIVE"))
                for field in ["name", "description"]:
                    if field not in fm:
                        result["warnings"].append(f"Frontmatter missing field: '{field}'")
                probe_cmd = fm.get("probe_cmd")
                if run_probes and probe_cmd:
                    # Rule #68 (golden interpreter): probe commands that use a bare
                    # `python3` must resolve to the canonical venv, never to a PATH
                    # shadow (audit R2: bare-`python3` probes compiled non-golden
                    # cpython pyc into lib/core/__pycache__).
                    probe_env = os.environ.copy()
                    venv_bin = os.path.join(vault_root, "and_os", ".venv", "bin")
                    if os.path.isdir(venv_bin):
                        probe_env["PATH"] = venv_bin + os.pathsep + probe_env.get("PATH", "")
                    p_res = subprocess.run(probe_cmd, shell=True, cwd=vault_root, env=probe_env, capture_output=True, text=True, timeout=3.0)
                    result["probe_result"] = {"cmd": probe_cmd, "success": p_res.returncode == 0}
                    if p_res.returncode != 0:
                        result["warnings"].append(f"Canary probe failed: {probe_cmd}")
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Read error: {e}")

        # 2. Symlink
        opencode_skills = os.path.join(vault_root, ".opencode", "skills")
        symlink_path = os.path.join(opencode_skills, skill_name)
        if not os.path.exists(symlink_path) and not os.path.islink(symlink_path):
            result["warnings"].append(f"Symlink missing: .opencode/skills/{skill_name}")

        # 3. Python compilation
        for root, _, files in os.walk(skill_path):
            for file in files:
                if file.endswith(".py"):
                    try:
                        script_path = os.path.join(root, file)
                        with tokenize.open(script_path) as source_file:
                            compile(source_file.read(), script_path, "exec")
                    except (SyntaxError, UnicodeError, OSError) as error:
                        result["valid"] = False
                        result["errors"].append(f"Python error in {file}: {error}")

        if result["errors"]:
            result["valid"] = False
        return result

    @classmethod
    def run(cls, vault_root: str, run_probes: bool = False, max_workers: int = 8, fix: bool = False, verbose: bool = True) -> BaseProbeResult:
        res = BaseProbeResult(name="Ring 3.5: Skill Operating Stack (SOS) Probe", ring=3)
        skills_dir = os.path.join(vault_root, "and_os", "lib", "skills")

        if not os.path.exists(skills_dir):
            res.passed = False
            res.issues_count = 1
            res.errors.append("and_os/lib/skills/ missing")
            return res

        skill_dirs = [
            (d, os.path.join(skills_dir, d))
            for d in os.listdir(skills_dir)
            if os.path.isdir(os.path.join(skills_dir, d)) and d not in IGNORE_DIRS
        ]

        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(cls.audit_single_skill, vault_root, s_name, s_path, run_probes): s_name
                for s_name, s_path in skill_dirs
            }
            for future in as_completed(future_map):
                results.append(future.result())

        invalid_skills = [r for r in results if not r["valid"]]
        warn_skills = [r for r in results if r["warnings"]]

        res.issues_count = len(invalid_skills)
        res.passed = (len(invalid_skills) == 0)
        res.details = {
            "total_skills": len(results),
            "valid_skills": len(results) - len(invalid_skills),
            "invalid_skills": len(invalid_skills),
            "warnings_skills": len(warn_skills)
        }

        for inv in invalid_skills:
            res.errors.append(f"Skill {inv['name']}: {', '.join(inv['errors'])}")

        return res
