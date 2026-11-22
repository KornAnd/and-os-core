#!/usr/bin/env python3
"""
gate_integrity_probe.py — Gate Integrity Probe for AnD os.

Detects WEAKENED QUALITY GATES: checks that silently stop failing.
Complements (does not duplicate) check_code_hygiene.py — the clean-code
guard owns code style across all files; this probe owns the integrity
of the verification gates themselves (tests, suppressions, timing):

  G1. Unjustified skips:    @pytest.mark.skip / xfail / pytest.skip()
                            without a reason argument.
  G2. Unspecific suppressions:  # noqa or # type: ignore without a
                            rule code (bare suppressions hide regressions).
  G3. Assertion-free tests: test functions containing no assert,
                            no raise, and no pytest.raises/fixture check.
  G4. Inflated timing:      time.sleep(N>5) or timeout=N>300 inside
                            test files (gates stretched past their budget).
  G5. Swallowed test failures: try/except Exception: pass inside a
                            test function (a gate that cannot fail).

Scan scope: Python files under the given roots (default: and_os/bin,
and_os/lib, and_os/tests), excluding .venv and vault_shadow.

Usage:
  python3 gate_integrity_probe.py [root ...]

Exit codes: 0 clean (0 findings) · 1 findings · 2 usage/environment error.
Read-only, no network, standard library only.
"""

import ast
import os
import re
import sys
from typing import Iterator

EXIT_CLEAN = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2

NOQA_BARE_RE = re.compile(r"#\s*noqa\s*$")
NOQA_CODED_RE = re.compile(r"#\s*noqa\s*(:|\[| )\s*[A-Z]")
TYPE_IGNORE_BARE_RE = re.compile(r"#\s*type:\s*ignore\s*$")
TYPE_IGNORE_CODED_RE = re.compile(r"#\s*type:\s*ignore\s*\[")
SLEEP_RE = re.compile(r"time\.sleep\(\s*(\d+(?:\.\d+)?)\s*\)")
TIMEOUT_RE = re.compile(r"timeout\s*=\s*(\d+(?:\.\d+)?)\s*[,)\n]")

SLEEP_BUDGET_SECONDS = 5.0
TIMEOUT_BUDGET_SECONDS = 300.0

EXCLUDED_DIRS = {".venv", "vault_shadow", "__pycache__", ".git"}


def fail_usage(message: str) -> None:
    sys.stderr.write(f"[gate_integrity_probe] ERROR: {message}\n")
    sys.exit(EXIT_USAGE)


def iter_python_files(roots: list) -> Iterator[str]:
    """Yields Python files under the roots (exclusions applied)."""
    for root in roots:
        if not os.path.isdir(root):
            fail_usage(f"scan root is not a directory: {root}")
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
            for name in filenames:
                if name.endswith(".py"):
                    yield os.path.join(dirpath, name)


def is_test_file(path: str) -> bool:
    return "/tests/" in path or path.startswith("tests/") \
        or os.path.basename(path).startswith("test_")


def scan_suppressions(path: str, lines: list, findings: list) -> None:
    """G2: bare # noqa / # type: ignore without a rule code."""
    for index, line in enumerate(lines, start=1):
        if NOQA_BARE_RE.search(line) and not NOQA_CODED_RE.search(line):
            findings.append((path, index, "G2", "bare # noqa (no rule code)"))
        if TYPE_IGNORE_BARE_RE.search(line) and \
                not TYPE_IGNORE_CODED_RE.search(line):
            findings.append(
                (path, index, "G2", "bare # type: ignore (no code)"))


def scan_timing(path: str, lines: list, findings: list) -> None:
    """G4: sleep/timeout beyond budget inside test files."""
    if not is_test_file(path):
        return
    for index, line in enumerate(lines, start=1):
        for match in SLEEP_RE.finditer(line):
            value = float(match.group(1))
            if value > SLEEP_BUDGET_SECONDS:
                findings.append(
                    (path, index, "G4",
                     f"time.sleep({value}) > {SLEEP_BUDGET_SECONDS}s budget"))
        for match in TIMEOUT_RE.finditer(line):
            value = float(match.group(1))
            if value > TIMEOUT_BUDGET_SECONDS:
                findings.append(
                    (path, index, "G4",
                     f"timeout={value}s > {TIMEOUT_BUDGET_SECONDS}s budget"))


def has_assertion(node: ast.AST) -> bool:
    """True when a test body asserts, raises, or uses a check fixture.

    Recognizes both harness styles: pytest (assert statements,
    pytest.raises) and unittest (self.assert* method calls).
    """
    for child in ast.walk(node):
        if isinstance(child, ast.Assert):
            return True
        if isinstance(child, ast.Raise):
            return True
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Attribute):
                if func.attr in ("raises", "warns", "deprecated_call"):
                    return True
                if func.attr.startswith("assert"):
                    return True
            if isinstance(func, ast.Name) and func.id in (
                    "assert_raises", "assertWarns", "check"):
                return True
    return False


def scan_ast(path: str, tree: ast.AST, findings: list) -> None:
    """G1 (skip/xfail), G3 (assertion-free), G5 (swallowed failures)."""
    is_test = is_test_file(path)
    for node in ast.walk(tree):
        # G1: skip/xfail decorators and calls without a reason.
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for deco in node.decorator_list:
                args = []
                keywords = []
                if isinstance(deco, ast.Call):
                    name = ast.unparse(deco.func)
                    args, keywords = deco.args, deco.keywords
                elif isinstance(deco, ast.Attribute):
                    name = ast.unparse(deco)
                else:
                    continue
                if not name.endswith(("mark.skip", "mark.xfail",
                                      "mark.skipif")):
                    continue
                has_reason = any(
                    isinstance(kw, ast.keyword)
                    and kw.arg in ("reason", "condition")
                    for kw in keywords)
                if name.endswith("mark.skipif"):
                    has_reason = len(args) >= 2 or has_reason
                if not has_reason:
                    findings.append(
                        (path, node.lineno, "G1",
                         f"{name} without reason in "
                         f"{node.name}()"))
        # G3: assertion-free test functions.
        if (is_test and isinstance(node, (ast.FunctionDef,
                                          ast.AsyncFunctionDef))
                and node.name.startswith("test_")
                and not has_assertion(node)):
            findings.append(
                (path, node.lineno, "G3",
                 f"assertion-free test: {node.name}()"))
        # G5: try/except Exception: pass inside test functions.
        if is_test and isinstance(node, ast.Try):
            for handler in node.handlers:
                if handler.type is None or (
                        isinstance(handler.type, ast.Name)
                        and handler.type.id in ("Exception", "BaseException")):
                    if any(isinstance(st, ast.Pass)
                           for st in handler.body):
                        findings.append(
                            (path, node.lineno, "G5",
                             "except Exception/...: pass inside test "
                             "(gate cannot fail)"))


def print_findings(findings: list) -> None:
    sys.stdout.write("\n" + "=" * 68 + "\n")
    sys.stdout.write("🛡️  Gate Integrity Probe (system-audit v1.1)\n")
    sys.stdout.write("=" * 68 + "\n")
    if not findings:
        sys.stdout.write("clean: no weakened gates detected\n")
        return
    by_class = {}
    for path, line, code, detail in findings:
        by_class.setdefault(code, []).append((path, line, detail))
    for code in sorted(by_class):
        items = by_class[code]
        sys.stdout.write(f"\n{code}: {len(items)} finding(s)\n")
        for path, line, detail in items[:30]:
            sys.stdout.write(f"   {path}:{line}  {detail}\n")
        if len(items) > 30:
            sys.stdout.write(f"   ... and {len(items) - 30} more\n")
    sys.stdout.write(f"\nSUMMARY: {len(findings)} weakened-gate "
                     f"finding(s) across {len(by_class)} class(es)\n")
    sys.stdout.write("=" * 68 + "\n")


def main(argv: list) -> int:
    roots = argv if argv else ["and_os/bin", "and_os/lib", "and_os/tests"]
    findings = []
    for path in iter_python_files(roots):
        try:
            with open(path, "r", encoding="utf-8",
                      errors="replace") as handle:
                lines = handle.read().splitlines()
        except OSError as err:
            fail_usage(f"cannot read {path}: {err}")
        scan_suppressions(path, lines, findings)
        scan_timing(path, lines, findings)
        try:
            tree = ast.parse("\n".join(lines), filename=path)
        except SyntaxError as err:
            fail_usage(f"syntax error in {path}:{err.lineno} "
                       f"(fix syntax before gate probing)")
        scan_ast(path, tree, findings)
    findings.sort(key=lambda item: (item[0], item[1]))
    print_findings(findings)
    return EXIT_FINDINGS if findings else EXIT_CLEAN


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
