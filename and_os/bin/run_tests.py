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
single-process design is restored.

Hermetic-FHS contract (Rule #50) enforced for the child process:
PYTHONDONTWRITEBYTECODE=1 is set in the environment BEFORE pytest starts,
so the suite leaves zero bytecode artifacts in the source tree.

Usage:
  run_tests.py                full suite, quiet (single pytest process)
  run_tests.py <path> ...     targeted test files (passed through to pytest)
  run_tests.py -v             verbose (any unknown argument is forwarded)
"""

import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
VAULT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
VENV_PYTHON = os.path.join(VAULT_ROOT, "and_os", ".venv", "bin", "python")

# Full-suite collection roots (audit R4, P1; B1: the cg Production
# Skeleton DoD moved into and_os/lib/core/cg/ and is collected here).
APP_AND_KERNEL_ROOTS = (
    os.path.join(VAULT_ROOT, "and_os", "tests"),
    os.path.join(VAULT_ROOT, "and_os", "lib", "core"),
)


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
    # Full suite: one pytest process (see module docstring: the B1
    # relocation resolved the top-level "core" collision that forced
    # the P11 split).
    res = subprocess.run(
        [interpreter] + list(PYTEST_BASE) + list(APP_AND_KERNEL_ROOTS),
        cwd=VAULT_ROOT, env=env)
    return res.returncode


if __name__ == "__main__":
    sys.exit(main())
