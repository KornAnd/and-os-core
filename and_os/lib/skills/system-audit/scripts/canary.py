#!/usr/bin/env python3
"""canary.py — High-speed smoke verification probe for system-audit.

In-memory syntax compile of every script in this skill's scripts/ tier
(no bytecode written, no subprocess, <500 ms budget per the EXECUTABLE_ENGINE
canary contract). Exit 0 = PASS, 1 = FAIL. Zero silent exceptions.
"""

import os
import sys
import time

sys.dont_write_bytecode = True  # Rule #71: never leak bytecode from a probe.

BUDGET_MS = 500


def compile_check(script_path: str) -> str:
    """Compile one script in memory; return a diagnostic string on failure."""
    try:
        with open(script_path, "r", encoding="utf-8") as handle:
            source = handle.read()
    except OSError as exc:
        return f"unreadable: {exc}"
    if not source.strip():
        return "empty file"
    try:
        compile(source, script_path, "exec")
    except SyntaxError as exc:
        return f"syntax error at line {exc.lineno}: {exc.msg}"
    return ""


def canary_test() -> int:
    started = time.perf_counter()
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    scripts = sorted(
        name for name in os.listdir(scripts_dir)
        if name.endswith(".py") and name != "canary.py"
    )
    if not scripts:
        sys.stderr.write("canary: no scripts/ payloads to verify\n")
        return 1

    failures = []
    for name in scripts:
        problem = compile_check(os.path.join(scripts_dir, name))
        if problem:
            failures.append(f"{name}: {problem}")
        else:
            print(f"  [  ok] {name} compiles")

    elapsed_ms = (time.perf_counter() - started) * 1000
    if failures:
        sys.stderr.write("canary: FAIL\n")
        for item in failures:
            sys.stderr.write(f"  [fail] {item}\n")
        return 1
    if elapsed_ms > BUDGET_MS:
        sys.stderr.write(f"canary: budget exceeded ({elapsed_ms:.0f} ms > {BUDGET_MS} ms)\n")
        return 1
    print(f"canary: PASS ({len(scripts)} scripts, {elapsed_ms:.0f} ms < {BUDGET_MS} ms)")
    return 0


if __name__ == "__main__":
    sys.exit(canary_test())
