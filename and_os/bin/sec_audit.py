#!/usr/bin/env python3
"""
sec_audit.py - Security Audit & OWASP Top-10 / Injection Scanner for AnD os.
Performs AST and heuristic analysis on Python, Swift, Shell, and Web codebase for:
  - Command Injection (subprocess with shell=True, os.system, eval/exec)
  - OWASP A01: Broken Access Control & SSRF (unvalidated external requests)
  - OWASP A03: Injection (SQL string concatenation, unescaped queries)
  - OWASP A07: Secrets & Credentials (hardcoded API keys, tokens, missing Keychain)
  - OWASP A09: Security Logging (passwords or tokens leaked into log statements)
  - Path Traversal (unvalidated relative directory traversal)
"""

import sys
import os
import ast
import re
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Dangerous constructs in Python AST
COMMAND_INJECTION_CALLS = {"system", "popen", "popen2", "popen3", "popen4"}

# Regex heuristics for fast multi-language scanning
SQLI_PATTERN = re.compile(r"""(?:["']\s*(?:SELECT|INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM|DROP\s+TABLE|ALTER\s+TABLE)\s+.*(?:%s|format\(|\+\s*[a-zA-Z_]|\{\w+\})|cursor\.execute\s*\(f?["'].*\{)""", re.IGNORECASE)
SECRET_ASSIGN_PATTERN = re.compile(r"""(?i)(?:api_key|secret|password|auth_token|access_token|private_key)\s*=\s*['\"][a-zA-Z0-9_\-\.]{8,}['\"]""")
SSRF_PATTERN = re.compile(r"""(?:requests\.(?:get|post|put|delete)|urllib\.request\.urlopen|aiohttp\.ClientSession)\s*\(\s*(?:request\.|params|args|url)""", re.IGNORECASE)
LOG_LEAK_PATTERN = re.compile(r"""(?:log(?:ging)?\.(?:debug|info|warn|warning|error)|print)\s*\(.*(?:password|token|secret|key|cred).*=.*\)""", re.IGNORECASE)

class SecurityAuditor:
    def __init__(self, target_dir: str):
        self.target_dir = Path(target_dir).resolve()
        self.findings = []
        self.files_scanned = 0

    def audit_python_ast(self, file_path: Path):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            tree = ast.parse(content, filename=str(file_path))
            lines = content.splitlines()
        except Exception:
            return

        rel_path = file_path.relative_to(self.target_dir)

        for node in ast.walk(tree):
            start_l = getattr(node, "lineno", 1) - 1
            end_l = getattr(node, "end_lineno", start_l + 1)
            node_lines = "\n".join(lines[start_l:end_l])
            if "# nosec" in node_lines or "# sec-ignore" in node_lines:
                continue

            # 1. Check eval / exec
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name in ("eval", "exec"):
                    self.findings.append({
                        "file": str(rel_path),
                        "line": node.lineno,
                        "severity": "CRITICAL",
                        "rule": "BANNED_EXEC_EVAL",
                        "desc": f"Direct use of {func_name}() allows arbitrary code execution"
                    })

                # 2. Check os.system / os.popen
                if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    if node.func.value.id == "os" and node.func.attr in COMMAND_INJECTION_CALLS:
                        self.findings.append({
                            "file": str(rel_path),
                            "line": node.lineno,
                            "severity": "HIGH",
                            "rule": "INSECURE_OS_CALL",
                            "desc": f"os.{node.func.attr}() is vulnerable to shell injection; use subprocess with list arguments"
                        })

                # 3. Check subprocess.*(..., shell=True)
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ("run", "Popen", "call", "check_output", "check_call"):
                        for kw in node.keywords:
                            if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                                # Inspect first arg for f-string or string formatting
                                arg0 = node.args[0] if node.args else None
                                is_dyn = isinstance(arg0, (ast.JoinedStr, ast.BinOp))
                                self.findings.append({
                                    "file": str(rel_path),
                                    "line": node.lineno,
                                    "severity": "CRITICAL" if is_dyn else "HIGH",
                                    "rule": "SHELL_TRUE_INJECTION",
                                    "desc": "subprocess called with shell=True" + (" and dynamic string interpolation!" if is_dyn else "")
                                })

    def audit_file_heuristics(self, file_path: Path):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            return

        rel_path = file_path.relative_to(self.target_dir)

        for idx, line in enumerate(lines, 1):
            line_str = line.strip()
            if not line_str or line_str.startswith("#") or line_str.startswith("//"):
                continue
            if "# nosec" in line_str or "# sec-ignore" in line_str:
                continue

            # SQL Injection check (exclude ftrack API queries or test mockups)
            prev_line = lines[idx - 2] if idx >= 2 else ""
            if "session.query" not in line_str and "session.query" not in prev_line and "ftrack" not in str(file_path).lower():
                if SQLI_PATTERN.search(line_str):
                    self.findings.append({
                        "file": str(rel_path),
                        "line": idx,
                        "severity": "HIGH",
                        "rule": "OWASP_A03_SQLI",
                        "desc": "Possible SQL dynamic string concatenation detected"
                    })

            # Hardcoded Secret check
            if SECRET_ASSIGN_PATTERN.search(line_str) and "@@K:" not in line_str and "test" not in str(file_path):
                self.findings.append({
                    "file": str(rel_path),
                    "line": idx,
                    "severity": "HIGH",
                    "rule": "OWASP_A07_HARDCODED_SECRET",
                    "desc": "Plaintext secret assignment detected; store credentials via macOS Keychain (@@K:)"
                })

            # SSRF check
            if SSRF_PATTERN.search(line_str):
                self.findings.append({
                    "file": str(rel_path),
                    "line": idx,
                    "severity": "MEDIUM",
                    "rule": "OWASP_A01_POTENTIAL_SSRF",
                    "desc": "External network call using untrusted parameters; validate URL against whitelist"
                })

            # Log Leak check
            if LOG_LEAK_PATTERN.search(line_str):
                self.findings.append({
                    "file": str(rel_path),
                    "line": idx,
                    "severity": "LOW",
                    "rule": "OWASP_A09_LOG_LEAK",
                    "desc": "Potential credential or token leakage in logging output"
                })

            # Path Traversal check
            if "../" in line_str and ("open(" in line_str or "Path(" in line_str or "readFile" in line_str):
                self.findings.append({
                    "file": str(rel_path),
                    "line": idx,
                    "severity": "MEDIUM",
                    "rule": "PATH_TRAVERSAL",
                    "desc": "Direct relative directory traversal '../' detected in file operations"
                })

    def run(self) -> Dict[str, Any]:
        ignore_dirs = {".git", ".trash", "venv", ".venv", "__pycache__", "node_modules", ".obsidian", "var", "checkpoints", "vault_shadow"}
        
        for root, dirs, files in os.walk(self.target_dir):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for file in files:
                p = Path(root) / file
                if p.suffix in (".py", ".swift", ".js", ".ts", ".sh"):
                    self.files_scanned += 1
                    if p.suffix == ".py":
                        self.audit_python_ast(p)
                    self.audit_file_heuristics(p)

        criticals = [f for f in self.findings if f["severity"] == "CRITICAL"]
        highs = [f for f in self.findings if f["severity"] == "HIGH"]
        mediums = [f for f in self.findings if f["severity"] == "MEDIUM"]
        lows = [f for f in self.findings if f["severity"] == "LOW"]

        passed = len(criticals) == 0 and len(highs) == 0

        return {
            "passed": passed,
            "files_scanned": self.files_scanned,
            "counts": {
                "critical": len(criticals),
                "high": len(highs),
                "medium": len(mediums),
                "low": len(lows),
                "total": len(self.findings)
            },
            "findings": self.findings
        }

def print_report(res: Dict[str, Any]):
    print("=" * 65)
    print(" 🛡️  AnD os Security Audit & OWASP Top-10 / Injection Scanner")
    print("=" * 65)
    print(f" Files Scanned   : {res['files_scanned']}")
    print(f" Status          : {'🟢 PASS' if res['passed'] else '🔴 FAIL (Vulnerabilities found)'}")
    print(f" Severity Breakdown: CRITICAL: {res['counts']['critical']} | HIGH: {res['counts']['high']} | MEDIUM: {res['counts']['medium']} | LOW: {res['counts']['low']}")
    print("-" * 65)
    
    if not res["findings"]:
        print(" ✨ No security vulnerabilities or OWASP violations detected!")
    else:
        for f in res["findings"]:
            sev_icon = "🔴" if f["severity"] in ("CRITICAL", "HIGH") else ("🟡" if f["severity"] == "MEDIUM" else "ℹ️")
            print(f" {sev_icon} [{f['severity']}] {f['file']}:{f['line']} -> {f['rule']}")
            print(f"    └─ {f['desc']}")
    print("=" * 65)

def main():
    parser = argparse.ArgumentParser(description="AnD os Security & OWASP Top-10 / Injection Scanner")
    parser.add_argument("path", nargs="?", default="and_os", help="Path or directory to scan (default: and_os)")
    args = parser.parse_args()

    auditor = SecurityAuditor(args.path)
    report = auditor.run()
    print_report(report)
    sys.exit(0 if report["passed"] else 1)

if __name__ == "__main__":
    main()
