#!/usr/bin/env python3
"""
run_tests.py — Canonical AnD os test-suite runner.

Single entrypoint for the full canonical suite (audit R4 P1; evolved in
P11; consolidated in B1). The full suite runs as ONE pytest process over
  (1) and_os/tests + and_os/lib/core — application layer + microkernel
      (R4-TEST-1: the legacy kernel tests were never collected before) +
      the cg Production Skeleton DoD (P11), which since the B1
      relocation lives in and_os/lib/core/cg/ and is collected with the
      kernel.
P11 split the suite into two isolated pytest processes because both I-1
test zones registered a top-level package named "core" (pytest prepend
import mode); the B1 relocation of the skeleton into the kernel zone and
the switch to kernel-qualified imports removed the collision, so the
single-process design was restored.

22.11 (P1b regression, split restored): the AND_Terminal P0/P1b security
extraction made server.py import the app's own top-level `core` package
(and_os/opt/terminal/core/ — the P11 collision class). Under pytest's
prepend import mode the kernel test zone maps to a top-level `core` as
well (and_os/lib/core/__init__.py exists while and_os/lib has none, so
its test modules import as `core.test_*`). The two `core` packages can
never coexist in one pytest process — the B1 single-process restoration
held only while no collected module pulled a top-level `core` into the
process. The P11 two-process split is restored: app/test zone and kernel
zone run in isolated pytest processes; both must pass.

Hermetic-FHS contract (Rule #50) enforced for the child process:
PYTHONDONTWRITEBYTECODE=1 is set in the environment BEFORE pytest starts,
so the suite leaves zero bytecode artifacts in the source tree.

C13 (F2): app-level tests under and_os/opt/apps/*/tests were invisible
to the canonical suite, so a live CG e2e regression (the "check"
UnboundLocalError) stayed red while the suite reported green. Every app
that ships a tests/ directory is now a collection root.

Usage:
  run_tests.py                full suite, quiet (single pytest process)
  run_tests.py <path> ...     targeted test files (passed through to pytest)
  run_tests.py -v             verbose (any unknown argument is forwarded)
"""

import glob
import os
import subprocess
import sys
sys.dont_write_bytecode = True  # Rule #71: no bytecode leaks from entrypoints.

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
VAULT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
VENV_PYTHON = os.path.join(VAULT_ROOT, "and_os", ".venv", "bin", "python")

# Full-suite collection roots (audit R4, P1; B1: the cg Production
# Skeleton DoD moved into and_os/lib/core/cg/ and is collected here;
# C13 F2: app tests/ directories joined the canonical suite).
# 22.11 (P11 split restored): the app/test zone and the kernel zone must
# run in isolated pytest processes — both map a top-level `core` package
# under pytest's prepend import mode (see module docstring).
APP_TEST_ROOTS = (
    os.path.join(VAULT_ROOT, "and_os", "tests"),
) + tuple(sorted(glob.glob(
    os.path.join(VAULT_ROOT, "and_os", "opt", "apps", "*", "tests")
)))
KERNEL_ROOT = os.path.join(VAULT_ROOT, "and_os", "lib", "core")
APP_AND_KERNEL_ROOTS = APP_TEST_ROOTS + (KERNEL_ROOT,)


# The suite must leave zero artifacts: PYTHONDONTWRITEBYTECODE (bytecode)
# and -p no:cacheprovider (the .pytest_cache directory, which would trip
# the root-hygiene gate, Rule #4/#7) are both enforced here.
PYTEST_BASE = ["-m", "pytest", "-q", "-p", "no:cacheprovider"]


def _forwarded_cmd(interpreter):
    """Build the child command for targeted invocations (args passed through)."""
    cmd = [interpreter] + list(PYTEST_BASE)
    for arg in sys.argv[1:]:
        if os.path.isabs(arg):
            cmd.append(arg)
        elif os.path.exists(os.path.join(VAULT_ROOT, arg)):
            cmd.append(os.path.join(VAULT_ROOT, arg))
        elif os.path.exists(os.path.join(VAULT_ROOT, "and_os", "tests", arg)):
            cmd.append(os.path.join(VAULT_ROOT, "and_os", "tests", arg))
        else:
            cmd.append(arg)
    return cmd


def main() -> int:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    interpreter = VENV_PYTHON if os.path.exists(VENV_PYTHON) else sys.executable
    if sys.argv[1:]:
        # Targeted mode: a single pytest process, arguments forwarded.
        res = subprocess.run(_forwarded_cmd(interpreter),
                             cwd=VAULT_ROOT, env=env)
        return res.returncode
    # Full suite: two isolated pytest processes (P11 architecture,
    # restored 22.11 after the P1b top-level `core` regression). Both
    # zones are run even when the first fails, so a single invocation
    # reports the full picture; the exit code is non-zero when either
    # zone is red.
    app_res = subprocess.run(
        [interpreter] + list(PYTEST_BASE) + list(APP_TEST_ROOTS),
        cwd=VAULT_ROOT, env=env)
    kernel_res = subprocess.run(
        [interpreter] + list(PYTEST_BASE) + [KERNEL_ROOT],
        cwd=VAULT_ROOT, env=env)
    if app_res.returncode != 0:
        print(f"[run_tests] app/test zone: FAILED (rc={app_res.returncode})")
    else:
        print("[run_tests] app/test zone: ok")
    if kernel_res.returncode != 0:
        print(f"[run_tests] kernel zone: FAILED (rc={kernel_res.returncode})")
    else:
        print("[run_tests] kernel zone: ok")
    return app_res.returncode or kernel_res.returncode


if __name__ == "__main__":
    sys.exit(main())
