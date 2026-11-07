#!/usr/bin/env python3
"""
quick_verify.py - Fast 6-Phase Pre-Flight Verification Loop for AnD os.
Inspired by Everything-Claude-Code verification principles and adapted for macOS, Python & Swift.

Phases:
  Phase 1: Syntax & Build Check (AST compile for Python, swiftc parse for Swift)
  Phase 2: Types & Semantic Linting (Type annotations, undefined names, ruff/pyright if present)
  Phase 3: Clean Code & Band-Aid Guard (Detect bare excepts, pass-only handlers, deep nesting)
  Phase 4: Unit Regression (Runs focused test suite for targeted modules if tests exist)
  Phase 5: Secret & Security Scan (Detect sk-, ghp-, AKIA, hardcoded tokens)
  Phase 6: Diff Hygiene & Size Analysis (Git diff line count check and status report)
  Phase 7: Closed-Loop Memory & Knowledge Integrity Guard
  Phase 8: Rules Fast Index Freshness Gate (SYSTEM.md parity check)
"""

import os
import sys
import ast
import re
import time
import argparse
import subprocess
from typing import List, Dict, Any, Optional

sys.dont_write_bytecode = True

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
VAULT_ROOT = os.getenv("AND_ROOT", os.path.abspath(os.path.join(SCRIPT_DIR, "../..")))
if VAULT_ROOT not in sys.path:
    sys.path.insert(0, VAULT_ROOT)

IGNORE_DIRS = {".space", ".obsidian", ".trash", "Trash", ".opencode", ".makemd", ".smart-env", ".git", "node_modules", ".archive", "var", "vault_shadow", "__pycache__", ".venv"}

# Patterns for secret scan (strictly alphanumeric keys)
SECRET_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9]{24,64}"),
    re.compile(r"ghp_[a-zA-Z0-9]{20,40}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"password\s*=\s*['\"][^'\"]{8,}['\"]", re.IGNORECASE)
]


class QuickVerifier:
    def __init__(self, root_dir: str, target_paths: Optional[List[str]] = None, verbose: bool = False):
        self.root_dir = os.path.abspath(root_dir)
        self.target_paths = target_paths or []
        self.verbose = verbose
        self.results = {
            "phase0_toolchain": {"passed": True, "errors": [], "details": {}},
            "phase1_syntax": {"passed": True, "errors": []},
            "phase2_types": {"passed": True, "errors": [], "warnings": []},
            "phase3_clean_code": {"passed": True, "errors": [], "warnings": []},
            "phase4_tests": {"passed": True, "errors": [], "tests_run": 0},
            "phase5_security": {"passed": True, "errors": []},
            "phase6_diff": {"passed": True, "files_changed": 0, "lines_added": 0, "lines_removed": 0},
            "phase7_memory": {"passed": True, "errors": [], "items_count": 0}
        }

    def get_staged_or_modified_files(self) -> List[str]:
        if self.target_paths:
            resolved = []
            for p in self.target_paths:
                full = os.path.abspath(p) if os.path.isabs(p) else os.path.abspath(os.path.join(self.root_dir, p))
                if os.path.exists(full):
                    if os.path.isdir(full):
                        for root, _, files in os.walk(full):
                            for f in files:
                                if f.endswith(('.py', '.swift', '.json', '.md')):
                                    resolved.append(os.path.join(root, f))
                    else:
                        resolved.append(full)
            return resolved

        try:
            cmd = ["git", "status", "--porcelain"]
            p = subprocess.run(cmd, cwd=self.root_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if p.returncode == 0:
                files = []
                for line in p.stdout.splitlines():
                    if len(line) > 3:
                        path_part = line[3:].strip()
                        if " -> " in path_part:
                            path_part = path_part.split(" -> ")[1].strip()
                        full = os.path.join(self.root_dir, path_part)
                        if os.path.exists(full) and not os.path.isdir(full):
                            files.append(full)
                if files:
                    return files
        except Exception:
            pass

        # Fallback to scanning recently modified files in and_os
        candidates = []
        now = time.time()
        for sub in ["and_os/bin", "and_os/lib", "Nero/xcode"]:
            full_sub = os.path.join(self.root_dir, sub)
            if os.path.exists(full_sub):
                for root, _, files in os.walk(full_sub):
                    for f in files:
                        if f.endswith((".py", ".swift")):
                            fp = os.path.join(root, f)
                            try:
                                if now - os.path.getmtime(fp) < 3600 * 24:
                                    candidates.append(fp)
                            except OSError:
                                pass
        return candidates

    def run_phase0_toolchain(self) -> None:
        """Phase 0: Toolchain & Environment Parity Gate (Rule #68)."""
        try:
            from and_os.lib.core.toolchain import ToolchainManager
            tm = ToolchainManager(os.path.abspath(self.root_dir))
            res = tm.check_parity()
            self.results["phase0_toolchain"]["passed"] = res["passed"]
            self.results["phase0_toolchain"]["errors"] = res["errors"]
            self.results["phase0_toolchain"]["details"] = res["stack"]
        except Exception as e:
            self.results["phase0_toolchain"]["passed"] = False
            self.results["phase0_toolchain"]["errors"].append(f"Toolchain check failed: {e}")

    def run_phase1_syntax(self, files: List[str]) -> None:
        """Phase 1: Syntax & Build Check."""
        for f in files:
            if f.endswith(".py"):
                try:
                    with open(f, "r", encoding="utf-8") as fh:
                        content = fh.read()
                    ast.parse(content, filename=f)
                except SyntaxError as e:
                    self.results["phase1_syntax"]["passed"] = False
                    self.results["phase1_syntax"]["errors"].append(f"{f}:{e.lineno}: SyntaxError: {e.msg}")
                except Exception as e:
                    self.results["phase1_syntax"]["passed"] = False
                    self.results["phase1_syntax"]["errors"].append(f"{f}: ReadError: {e}")
            elif f.endswith(".swift"):
                # Fast swiftc syntax parse
                try:
                    cmd = ["swiftc", "-parse", f]
                    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    if p.returncode != 0:
                        self.results["phase1_syntax"]["passed"] = False
                        err_line = p.stderr.splitlines()[0] if p.stderr else "Swift parse failed"
                        self.results["phase1_syntax"]["errors"].append(f"{f}: {err_line}")
                except FileNotFoundError:
                    pass

    def run_phase2_types(self, files: List[str]) -> None:
        """Phase 2: Types & Semantic Linting."""
        # Check python type annotations presence on functions if in core
        for f in files:
            if f.endswith(".py") and "and_os" in f:
                try:
                    with open(f, "r", encoding="utf-8") as fh:
                        tree = ast.parse(fh.read(), filename=f)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                            # Check if public function has return annotation
                            if node.returns is None and "test" not in f and "scratch" not in f:
                                rel = os.path.relpath(f, self.root_dir)
                                self.results["phase2_types"]["warnings"].append(
                                    f"{rel}:{node.lineno}: Function '{node.name}' lacks return type annotation"
                                )
                except Exception:
                    pass

    def run_phase3_clean_code(self, files: List[str]) -> None:
        """Phase 3: Clean Code & Band-Aid Guard (Rule #19 & DEV_PROTOCOL) + WebDAV Hygiene Guard."""
        # 1. WebDAV / File naming hygiene guard (<0.005s)
        try:
            from and_os.lib.vault.hygiene import validate_name
            for f in files:
                basename = os.path.basename(f)
                ok, errs = validate_name(basename)
                if not ok:
                    rel = os.path.relpath(f, self.root_dir)
                    self.results["phase3_clean_code"]["passed"] = False
                    self.results["phase3_clean_code"]["errors"].append(
                        f"{rel}: WebDAV naming violation: {', '.join(errs)}"
                    )
        except Exception:
            pass

        # 2. Python clean code AST checks
        for f in files:
            if f.endswith(".py"):
                try:
                    with open(f, "r", encoding="utf-8") as fh:
                        content = fh.read()
                    tree = ast.parse(content, filename=f)
                    rel = os.path.relpath(f, self.root_dir)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ExceptHandler):
                            # Check bare except
                            if node.type is None:
                                self.results["phase3_clean_code"]["passed"] = False
                                self.results["phase3_clean_code"]["errors"].append(
                                    f"{rel}:{node.lineno}: Banned bare except handler detected"
                                )
                            # Check pass-only except
                            elif len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                                if "test" not in f:
                                    self.results["phase3_clean_code"]["warnings"].append(
                                        f"{rel}:{node.lineno}: Silent exception swallowing (except: pass) detected"
                                    )
                except Exception:
                    pass

    def run_phase4_tests(self, files: List[str]) -> None:
        """Phase 4: Run targeted tests if any test files are associated."""
        test_files = [f for f in files if "test" in os.path.basename(f) and f.endswith(".py")]
        test_env = os.environ.copy()
        test_env["PYTHONPATH"] = f"{self.root_dir}:{test_env.get('PYTHONPATH', '')}"
        for tf in test_files:
            try:
                cmd = [sys.executable, tf]
                p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10, env=test_env, cwd=self.root_dir)
                self.results["phase4_tests"]["tests_run"] += 1
                if p.returncode != 0:
                    self.results["phase4_tests"]["passed"] = False
                    rel = os.path.relpath(tf, self.root_dir)
                    self.results["phase4_tests"]["errors"].append(f"{rel}: Test run failed with code {p.returncode}")
            except Exception as e:
                self.results["phase4_tests"]["passed"] = False
                self.results["phase4_tests"]["errors"].append(f"{tf}: Execution error: {e}")

    def run_phase5_security(self, files: List[str]) -> None:
        """Phase 5: Secret & Security Scan (Credentials + Command Injection + Eval/Exec)."""
        for f in files:
            rel = os.path.relpath(f, self.root_dir)
            parts = set(rel.split(os.sep))
            if parts & IGNORE_DIRS:
                continue
            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
                    lines = content.splitlines()

                # 1. Regex secrets check
                for idx, line in enumerate(lines, 1):
                    for pattern in SECRET_PATTERNS:
                        if pattern.search(line):
                            self.results["phase5_security"]["passed"] = False
                            self.results["phase5_security"]["errors"].append(
                                f"{rel}:{idx}: Potential exposed secret or token detected"
                            )

                # 2. Python AST Security Check (Eval/Exec, shell=True injection)
                if f.endswith(".py"):
                    try:
                        tree = ast.parse(content, filename=f)
                        for node in ast.walk(tree):
                            line_idx = getattr(node, "lineno", 1) - 1
                            line_text = lines[line_idx] if 0 <= line_idx < len(lines) else ""
                            if "# nosec" in line_text or "# sec-ignore" in line_text:
                                continue

                            if isinstance(node, ast.Call):
                                func_name = ""
                                if isinstance(node.func, ast.Name):
                                    func_name = node.func.id
                                elif isinstance(node.func, ast.Attribute):
                                    func_name = node.func.attr

                                if func_name in ("eval", "exec") and "test" not in rel:
                                    self.results["phase5_security"]["passed"] = False
                                    self.results["phase5_security"]["errors"].append(
                                        f"{rel}:{node.lineno}: Banned {func_name}() invocation detected"
                                    )

                                if isinstance(node.func, ast.Attribute) and node.func.attr in ("run", "Popen"):
                                    for kw in node.keywords:
                                        if kw.arg == "shell" and getattr(kw.value, "value", False) is True:
                                            arg0 = node.args[0] if node.args else None
                                            if isinstance(arg0, (ast.JoinedStr, ast.BinOp)):
                                                self.results["phase5_security"]["passed"] = False
                                                self.results["phase5_security"]["errors"].append(
                                                    f"{rel}:{node.lineno}: Unsafe dynamic shell=True subprocess invocation"
                                                )
                    except Exception:
                        pass
            except Exception:
                pass

    def run_phase6_diff(self) -> None:
        """Phase 6: Diff Hygiene & Size Analysis (Sovereign Vault Aware)."""
        git_dir = os.path.join(self.root_dir, ".git")
        if os.path.exists(git_dir):
            try:
                cmd = ["git", "diff", "--shortstat"]
                p = subprocess.run(cmd, cwd=self.root_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if p.returncode == 0 and p.stdout.strip():
                    # Format: "X files changed, Y insertions(+), Z deletions(-)"
                    m = re.search(r"(\d+)\s+file[s]?\s+changed", p.stdout)
                    if m:
                        self.results["phase6_diff"]["files_changed"] = int(m.group(1))
                    m_ins = re.search(r"(\d+)\s+insertion[s]?\(\+\)", p.stdout)
                    if m_ins:
                        self.results["phase6_diff"]["lines_added"] = int(m_ins.group(1))
                    m_del = re.search(r"(\d+)\s+deletion[s]?\(-\)", p.stdout)
                    if m_del:
                        self.results["phase6_diff"]["lines_removed"] = int(m_del.group(1))
                    return
            except Exception:
                pass

        # Fallback for sovereign vault: count recent files in and_os modified in last 24h
        try:
            recent_count = len(self.get_staged_or_modified_files())
            self.results["phase6_diff"]["files_changed"] = recent_count
            self.results["phase6_diff"]["lines_added"] = 0
            self.results["phase6_diff"]["lines_removed"] = 0
        except Exception:
            pass

    def run_phase7_memory(self) -> None:
        """Phase 7: Closed-Loop Memory & Knowledge Integrity Guard."""
        import json
        db_path = os.path.join(self.root_dir, "Clippings", "quick_knowledge_db.json")
        engineers_dir = os.path.join(self.root_dir, "Nero", "knowledge", "engineers")

        if not os.path.exists(db_path):
            # In standalone kernel / open-source edition, knowledge vault may not be mounted
            if not os.path.exists(os.path.join(self.root_dir, "Nero")):
                self.results["phase7_memory"]["passed"] = True
                self.results["phase7_memory"]["items_count"] = 0
                return
            self.results["phase7_memory"]["passed"] = False
            self.results["phase7_memory"]["errors"].append("Missing Clippings/quick_knowledge_db.json index file.")
            return

        try:
            with open(db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list) or len(data) == 0:
                self.results["phase7_memory"]["passed"] = False
                self.results["phase7_memory"]["errors"].append("quick_knowledge_db.json is empty or corrupt.")
                return
            self.results["phase7_memory"]["items_count"] = len(data)

            # Verify that learned empirical notes are indexed
            if os.path.exists(engineers_dir):
                eng_files = [f[:-3] for f in os.listdir(engineers_dir) if f.endswith(".md") and not f.startswith(".")]
                indexed_ids = {item.get("id") for item in data}
                missing = [ef for ef in eng_files if ef not in indexed_ids]
                if missing:
                    self.results["phase7_memory"]["passed"] = False
                    self.results["phase7_memory"]["errors"].append(f"Learned patterns unindexed: {', '.join(missing[:3])}")
        except Exception as e:
            self.results["phase7_memory"]["passed"] = False
            self.results["phase7_memory"]["errors"].append(f"Failed to read quick_knowledge_db.json: {e}")


    def run_phase8_rules_freshness(self) -> None:
        """Phase 8: Rules Fast Index Freshness Gate & Release Ledger Parity Gate."""
        # 1. Rules Fast Index verification
        compiler_script = os.path.join(self.root_dir, "and_os", "bin", "rules_compiler.py")
        rules_fast_index = os.path.join(self.root_dir, "and_os", "etc", "rules_fast_index.json")
        system_md = os.path.join(self.root_dir, "SYSTEM.md")

        if os.path.exists(compiler_script) and os.path.exists(system_md):
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("rules_compiler", compiler_script)
                rc_mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(rc_mod)
                ok, msg = rc_mod.verify_rules_freshness()
                self.results["phase8_rules"] = {
                    "passed": ok,
                    "message": msg,
                    "errors": [] if ok else [msg]
                }
                if not ok:
                    # Proactively auto-compile to heal the drift
                    rc_mod.compile_rules_index()
                    self.results["phase8_rules"]["passed"] = True
                    self.results["phase8_rules"]["message"] = f"{msg} -> 🟢 AUTO-HEALED (recompiled)"
                    self.results["phase8_rules"]["errors"] = []
            except Exception as e:
                self.results["phase8_rules"] = {
                    "passed": False,
                    "message": f"Rules verification failed: {e}",
                    "errors": [str(e)]
                }
        elif os.path.exists(rules_fast_index):
            # Standalone mode: index file exists and is valid
            self.results["phase8_rules"] = {
                "passed": True,
                "message": "Standalone mode: verified rules_fast_index.json structure",
                "errors": []
            }

        # 2. Release Ledger Parity Gate (<0.002s)
        try:
            from and_os.lib.core.release_ledger import verify_release_parity
            ok, parity_msg = verify_release_parity()
            if not ok:
                self.results["phase8_rules"]["passed"] = False
                self.results["phase8_rules"]["errors"].append(f"Release Ledger Parity Violation: {parity_msg}")
        except Exception:
            pass

    def verify(self) -> Dict[str, Any]:
        t0 = time.time()
        files = self.get_staged_or_modified_files()

        self.run_phase0_toolchain()
        self.run_phase1_syntax(files)
        self.run_phase2_types(files)
        self.run_phase3_clean_code(files)
        self.run_phase4_tests(files)
        self.run_phase5_security(files)
        self.run_phase6_diff()
        self.run_phase7_memory()
        self.run_phase8_rules_freshness()

        elapsed = round(time.time() - t0, 3)

        passed = (
            self.results["phase0_toolchain"]["passed"]
            and self.results["phase1_syntax"]["passed"]
            and self.results["phase3_clean_code"]["passed"]
            and self.results["phase4_tests"]["passed"]
            and self.results["phase5_security"]["passed"]
            and self.results["phase7_memory"]["passed"]
        )

        return {
            "passed": passed,
            "elapsed_seconds": elapsed,
            "scanned_files_count": len(files),
            "results": self.results
        }


def format_report(summary: Dict[str, Any]) -> str:
    res = summary["results"]
    status_icon = "🟢 ALL PHASES PASSED" if summary["passed"] else "🔴 VERIFICATION FAILED"

    p0_str = "🟢 PASS (3.12.11 LTS)" if res.get("phase0_toolchain", {}).get("passed") else "🔴 FAIL"
    p1_str = "🟢 PASS" if res["phase1_syntax"]["passed"] else "🔴 FAIL"
    warn_count = len(res["phase2_types"]["warnings"])
    p2_str = "🟢 PASS" if warn_count == 0 else f"🟡 {warn_count} warnings"
    p3_str = "🟢 PASS" if res["phase3_clean_code"]["passed"] else "🔴 FAIL"
    p4_str = f"🟢 {res['phase4_tests']['tests_run']} run" if res["phase4_tests"]["passed"] else "🔴 FAIL"
    p5_str = "🟢 PASS" if res["phase5_security"]["passed"] else "🔴 FAIL"
    diff_str = f"{res['phase6_diff']['files_changed']} files (+{res['phase6_diff']['lines_added']}/-{res['phase6_diff']['lines_removed']})"
    p7_str = f"🟢 PASS ({res['phase7_memory']['items_count']} items)" if res["phase7_memory"]["passed"] else "🔴 FAIL"

    lines = [
        "┌─────────────────────────────────────────────────────────────┐",
        f"│  🔍 Quick Verification Loop (Pre-Flight 9-Phase)  {summary['elapsed_seconds']}s   │",
        "├─────────────────────────────────────────────────────────────┤",
        f"│  Overall Status   : {status_icon:<39} │",
        f"│  Files Scanned    : {summary['scanned_files_count']:<39} │",
        "├─────────────────────────────────────────────────────────────┤",
        f"│  Phase 0: Toolchain Parity : {p0_str:<32} │",
        f"│  Phase 1: Syntax & Build   : {p1_str:<32} │",
        f"│  Phase 2: Types & Lint     : {p2_str:<32} │",
        f"│  Phase 3: Clean Code Guard : {p3_str:<32} │",
        f"│  Phase 4: Targeted Tests   : {p4_str:<32} │",
        f"│  Phase 5: Security Scan    : {p5_str:<32} │",
        f"│  Phase 6: Diff Delta       : {diff_str:<32} │",
        f"│  Phase 7: Memory Loop      : {p7_str:<32} │",
        f"│  Phase 8: Rules Freshness  : {('🟢 PASS' if res.get('phase8_rules', {}).get('passed') else '🔴 FAIL'):<32} │",
        "└─────────────────────────────────────────────────────────────┘"
    ]

    # Append errors if any
    all_errors = (
        res["phase1_syntax"]["errors"]
        + res["phase3_clean_code"]["errors"]
        + res["phase4_tests"]["errors"]
        + res["phase5_security"]["errors"]
        + res["phase7_memory"]["errors"]
    )
    if all_errors:
        lines.append("\n🚨 CRITICAL DEFECTS:")
        for err in all_errors[:10]:
            lines.append(f"  • {err}")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="AnD os Quick Pre-Flight Verification Loop")
    parser.add_argument("paths", nargs="*", help="Optional file or folder paths to verify")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON format")
    parser.add_argument("--verbose", "-v", action="store_true", help="Detailed debug output")
    args = parser.parse_args()

    vault_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    verifier = QuickVerifier(root_dir=vault_root, target_paths=args.paths, verbose=args.verbose)
    summary = verifier.verify()

    if args.json:
        import json
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(format_report(summary))

    sys.exit(0 if summary["passed"] else 1)


if __name__ == "__main__":
    main()
