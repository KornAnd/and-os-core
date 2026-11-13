"""
clean_code_probe.py — Ring 2.5: Clean Code Guardian & AST Quality Probe (Uncle Bob Protocol).
Part of AnD os System Infrastructure (and_os/lib/health_grid/).

Evaluates the Python codebase against the clean-code-guardian skill
criteria. Scope, exclusions and per-class severity are driven by
and_os/etc/probe_policy.json (probes.clean_code; audit R4, P4, R4-CC-1):

  1. Anti-Band-Aid Gate (silent excepts with a pass-only body):
     - bare_except_pass        (except: pass)             -> error
     - except_exception_pass   (except Exception: pass)   -> error
     - typed_except_pass       (except OSError: pass, ..) -> advisory
     Zone overrides allow a phase-gated severity downgrade: the legacy
     opt/ exc_pass backlog is advisory until the R4-CC-1 triage phase
     promotes it (see the triage doc referenced in the policy).
  2. Nesting & Depth Gate: max 4 levels in non-dispatcher functions —
     advisory (visibility only, never flips the ring).
  3. Deterministic full scan: every in-scope file is audited on every
     run. The legacy git-delta / mtime-24h branches were dead weight:
     the vault has no git tracking (Rule #67) and the mtime window
     silently dropped opt/ — 90 silent excepts lived outside the gate.

Advisory semantics (R3-F6-1 precedent): advisories are emitted as
warnings + details but do NOT increment issues_count, so the ring never
flips on advisory-only findings.
"""

import os
import ast
import json
import sys
from typing import Dict, Any, List, Tuple

from and_os.lib.health_grid import BaseProbeResult

# Directories that never contain audited production code
IGNORE_DIRS = {
    ".space", ".obsidian", ".trash", "Trash", ".opencode", ".makemd",
    ".smart-env", ".git", "node_modules", ".archive",
    "var", ".venv", "checkpoints", "__pycache__", "vault_shadow", "backups",
}
EXEMPT_DISPATCHERS = {"main", "cli_main", "run", "cmd_", "_execute"}

POLICY_REL_PATH = os.path.join("and_os", "etc", "probe_policy.json")

# Used when the policy file is absent or unreadable — the probe degrades
# to the R4-approved defaults and announces the fallback on stderr.
DEFAULT_POLICY: Dict[str, Any] = {
    "scope": ["and_os/bin", "and_os/lib", "and_os/sbin", "and_os/opt"],
    "exclude": ["and_os/lib/core"],
    "severity": {
        "bare_except_pass": "error",
        "except_exception_pass": "error",
        "typed_except_pass": "advisory",
    },
    "zone_overrides": {
        "and_os/opt": {"except_exception_pass": "advisory"},
    },
}


def get_max_nesting_depth(node: ast.AST, current_depth: int = 0) -> int:
    """Calculates maximum block nesting depth inside a function, treating if/elif/else chain as a single nesting level."""
    max_d = current_depth

    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.For, ast.While, ast.AsyncFor, ast.With, ast.AsyncWith)):
            d = get_max_nesting_depth(child, current_depth + 1)
            if d > max_d:
                max_d = d
        elif isinstance(child, ast.If):
            # Check if-body
            for b in child.body:
                d = get_max_nesting_depth(b, current_depth + 1)
                if d > max_d:
                    max_d = d
            # Flatten if-elif-else chain so elif does not artificially increment nesting depth
            cur_else = child.orelse
            while cur_else and len(cur_else) == 1 and isinstance(cur_else[0], ast.If):
                elif_node = cur_else[0]
                for b in elif_node.body:
                    d = get_max_nesting_depth(b, current_depth + 1)
                    if d > max_d:
                        max_d = d
                cur_else = elif_node.orelse
            if cur_else:
                for b in cur_else:
                    d = get_max_nesting_depth(b, current_depth + 1)
                    if d > max_d:
                        max_d = d
        elif not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            d = get_max_nesting_depth(child, current_depth)
            if d > max_d:
                max_d = d
    return max_d


def load_policy(vault_root: str) -> Dict[str, Any]:
    """Loads the clean_code section of the probe policy (with R4 defaults)."""
    policy: Dict[str, Any] = {k: (dict(v) if isinstance(v, dict) else list(v)) for k, v in DEFAULT_POLICY.items()}
    path = os.path.join(vault_root, POLICY_REL_PATH)
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        cc = raw.get("probes", {}).get("clean_code", {})
        for key in ("scope", "exclude", "severity", "zone_overrides"):
            if key in cc:
                policy[key] = cc[key]
    except (OSError, json.JSONDecodeError) as e:
        sys.stderr.write(f"[clean_code_probe] Notice: policy unreadable ({e}), using R4 defaults\n")
    return policy


def classify_handler(node: ast.ExceptHandler) -> Tuple[str, str]:
    """Classifies a pass-only except handler.

    Returns (class_name, exc_label):
      bare_except_pass        — no type at all
      except_exception_pass   — Name/Tuple composed only of
                                Exception / BaseException
      typed_except_pass       — any other type (OSError,
                                json.JSONDecodeError, tuples with
                                concrete types, ...)
    """
    t = node.type
    if t is None:
        return "bare_except_pass", "<bare>"
    if isinstance(t, ast.Name):
        names = [t.id]
    elif isinstance(t, ast.Tuple):
        names = [ast.unparse(e) for e in t.elts]
    else:
        return "typed_except_pass", ast.unparse(t)
    label = "/".join(names)
    if set(names) <= {"Exception", "BaseException"}:
        return "except_exception_pass", label
    return "typed_except_pass", label


def _zone_of(rel_p: str, scope: List[str]) -> str:
    """The first scope zone the (vault-relative) file path belongs to."""
    for z in scope:
        if rel_p == z or rel_p.startswith(z + os.sep):
            return z
    return ""


class CleanCodeProbe:
    @staticmethod
    def run(vault_root: str, fix: bool = False, verbose: bool = True) -> BaseProbeResult:
        result = BaseProbeResult(name="Ring 2.5: Clean Code Guardian Probe", ring=2)

        policy = load_policy(vault_root)
        scope: List[str] = policy["scope"]
        exclude: List[str] = policy.get("exclude", [])
        severity: Dict[str, str] = policy.get("severity", DEFAULT_POLICY["severity"])
        overrides: Dict[str, Dict[str, str]] = policy.get("zone_overrides", {})

        # Deterministic full scan of every in-scope production .py file
        files: List[str] = []
        for sub in scope:
            sub_p = os.path.join(vault_root, sub)
            if not os.path.isdir(sub_p):
                continue
            for r, dirs, fs in os.walk(sub_p):
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
                for f in fs:
                    if f.endswith(".py") and not f.startswith("test_") and f != "conftest.py":
                        files.append(os.path.join(r, f))

        error_sites: List[str] = []
        advisory_sites: List[str] = []
        nesting_advisories: List[str] = []
        total_functions = 0
        audited = 0

        for fpath in files:
            rel_p = os.path.relpath(fpath, vault_root)
            if any(rel_p == ex or rel_p.startswith(ex + os.sep) for ex in exclude):
                continue
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                    tree = ast.parse(fp.read(), filename=fpath)
            except (OSError, SyntaxError) as e:
                # Syntax breakage is Ring 0's job; announce so this probe
                # never audits a blind spot silently
                sys.stderr.write(f"[clean_code_probe] Notice: skipping {rel_p} ({e})\n")
                continue
            audited += 1
            zone = _zone_of(rel_p, scope)

            for node in ast.walk(tree):
                # 1. Anti-Band-Aid Check: silent excepts (pass-only body)
                if isinstance(node, ast.ExceptHandler):
                    if not (len(node.body) == 1 and isinstance(node.body[0], ast.Pass)):
                        continue
                    cls, label = classify_handler(node)
                    sev = severity.get(cls, "advisory")
                    if zone and cls in overrides.get(zone, {}):
                        sev = overrides[zone][cls]
                    site = f"{rel_p}:L{node.lineno} except {label}: pass"
                    if sev == "error":
                        error_sites.append(site)
                    else:
                        advisory_sites.append(site)

                # 2. Nesting & depth inspection
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    total_functions += 1
                    is_dispatcher = any(ex in node.name for ex in EXEMPT_DISPATCHERS) or node.name.startswith("cmd_")
                    if not is_dispatcher:
                        depth = get_max_nesting_depth(node)
                        if depth > 4:
                            nesting_advisories.append(f"{rel_p} -> {node.name}() depth={depth} (max allowed 4)")

        if error_sites:
            result.errors.append(
                f"Clean Code Gate Breach (Uncle Bob Rule): {len(error_sites)} silent exception(s) "
                f"in in-scope code: {error_sites[:5]}")
        if advisory_sites:
            result.warnings.append(
                f"Silent except advisory (no issues_count increment): {len(advisory_sites)} "
                f"pass-only sites, e.g. {advisory_sites[:3]}")
        if nesting_advisories:
            result.warnings.append(
                f"Deep Nesting Advisory (>4 levels): {len(nesting_advisories)} functions, "
                f"e.g. {nesting_advisories[:2]}")

        # Advisory semantics (R3-F6-1): only errors increment issues_count
        result.issues_count = len(result.errors)
        result.passed = len(result.errors) == 0
        result.details = {
            "files_audited": audited,
            "functions_audited": total_functions,
            "silent_except_errors": len(error_sites),
            "silent_except_advisories": len(advisory_sites),
            "deep_nesting_advisories": len(nesting_advisories),
            "error_sites": error_sites,
            "advisory_sites": advisory_sites,
        }

        return result
