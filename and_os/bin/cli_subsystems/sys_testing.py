"""Testing subsystem — canonical hermetic test-suite runner.
Exposes `sys_cli test`: runs the AnD os suite through and_os/bin/run_tests.py
so that PYTHONDONTWRITEBYTECODE=1 is enforced before any import (Rule #50
FHS gate: zero bytecode artifacts in the source tree).
"""

import sys
from typing import Any
from and_os.bin.cli_subsystems.base import BaseSubsystem, run_script, auto_log_telemetry


class TestingSubsystem(BaseSubsystem):
    name = "testing"
    description = "Canonical test-suite runner (hermetic FHS: zero bytecode artifacts)"

    @classmethod
    def register_subparsers(cls, subparsers) -> None:
        p_test = subparsers.add_parser(
            "test",
            help="Canonical test-suite run (pytest and_os/tests, PYTHONDONTWRITEBYTECODE=1)"
        )
        p_test.add_argument(
            "args", nargs="*",
            help="pytest arguments: targeted test paths, flags (-v, -x, ...)"
        )

    @classmethod
    def execute(cls, args: Any) -> int:
        flags = list(getattr(args, "args", []) or [])
        res = run_script("run_tests.py", flags)
        print(res.get("stdout", ""), end="")
        if res.get("stderr"):
            print(res["stderr"], file=sys.stderr)
        auto_log_telemetry(f"Test suite run: {flags or 'full'}", skill="sys.test")
        return res.get("returncode", 0)
