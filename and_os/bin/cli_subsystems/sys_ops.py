"""Operations Subsystem (ops): dispatcher wiring of the standalone utilities.
Modular extension of sys_cli.py following Clean Architecture (Uncle Bob).
C10c: closes the Ring-2 advisory for the 4 scripts in and_os/bin without a
dispatcher entry (export_kernel, web_perf_baseline, tg_career_fetcher,
publish_doc) through external composition — the kernel sys_cli.py is not modified.
"""

import sys
from typing import Any
from and_os.bin.cli_subsystems.base import BaseSubsystem, run_script, auto_log_telemetry


class OpsSubsystem(BaseSubsystem):
    name = "ops"
    description = "One-shot operational utilities: kernel export, web perf baseline, Telegram career fetcher, document publication"

    # action -> companion script in and_os/bin (Rule #54 holistic binding:
    # perf-baseline = ui-inspector engine, tg-career = career-radar engine,
    # publish-doc = document-hub engine, export-kernel = release pipeline)
    ACTION_SCRIPT_MAP = {
        "export-kernel": "export_kernel.py",
        "perf-baseline": "web_perf_baseline.py",
        "tg-career": "tg_career_fetcher.py",
        "publish-doc": "publish_doc.py",
    }

    @classmethod
    def register_subparsers(cls, subparsers) -> None:
        p_ops = subparsers.add_parser(
            "ops",
            help="The one-shot operational utilities (export-kernel, perf-baseline, tg-career, publish-doc)")
        p_ops.add_argument("action", choices=sorted(cls.ACTION_SCRIPT_MAP), help="The utility action")
        p_ops.add_argument("extra_args", nargs="*", help="The arguments of the target utility")

    @classmethod
    def execute(cls, args: Any) -> int:
        target_script = cls.ACTION_SCRIPT_MAP.get(args.action)
        if not target_script:
            print(f"[!] Unknown ops action: {args.action}", file=sys.stderr)
            return 1
        res = run_script(target_script, args.extra_args or [])
        print(res.get("stdout", ""), end="")
        if res.get("stderr"):
            print(res["stderr"], file=sys.stderr)
        auto_log_telemetry(f"Ops utility run: {args.action}", skill="sys.ops")
        return res.get("returncode", 0)
