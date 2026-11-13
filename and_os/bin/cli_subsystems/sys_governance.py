"""Governance and Quality Verification subsystem (verify, audit, eval, tdd, sec-audit, rules).
Modular extraction from sys_cli.py following Clean Architecture (Uncle Bob).
Enforces Rule #65 (Zero Broken Windows Gate), Rule #61 (Zero-Blind-Assumptions), and Rule #68 (Toolchain Parity).
"""

import sys
from typing import Any
from and_os.bin.cli_subsystems.base import BaseSubsystem, run_script, auto_log_telemetry


class GovernanceSubsystem(BaseSubsystem):
    name = "governance"
    description = "Quality gate, security audit, pre-flight verification, eval, and rules compiler"

    @classmethod
    def register_subparsers(cls, subparsers) -> None:
        # verify
        p_ver = subparsers.add_parser("verify", help="8-phase pre-commit quality filter (syntax, types, clean code, secrets, tests, diff, memory, rules)")
        p_ver.add_argument("paths", nargs="*", help="Files or directories for pinpoint verification")
        p_ver.add_argument("--json", action="store_true", help="Machine-readable JSON output")
        p_ver.add_argument("--verbose", "-v", action="store_true", help="Expanded report output")

        # audit
        p_audit = subparsers.add_parser("audit", help="Run the 16-vector audit of the AnD os v1.0.0 system")
        p_audit.add_argument("--fix", action="store_true", help="Automatic repair of basic errors (L1-L3)")
        p_audit.add_argument("--compact", action="store_true", help="Compact output to save context")
        p_audit.add_argument("--json", action="store_true", help="JSON format output")
        p_audit.add_argument("--read-only", action="store_true", help="Run without writing bytecode")

        # eval
        p_eval = subparsers.add_parser("eval", help="Eval-Driven Development framework (pass@1, pass@3 metrics, regression control)")
        p_eval.add_argument("action", choices=["define", "check", "list"], help="Action: define, check, list")
        p_eval.add_argument("feature", nargs="?", help="Feature or system name")
        p_eval.add_argument("--desc", default="", help="Requirements description")
        p_eval.add_argument("--domain", default="core", help="System domain")

        # tdd
        p_tdd = subparsers.add_parser("tdd", help="Generator of modular test skeletons (Python unittest / Swift XCTest)")
        p_tdd.add_argument("file", help="Source file for test generation (.py or .swift)")
        p_tdd.add_argument("--out", "-o", help="Custom save path for the test")
        p_tdd.add_argument("--run", "-r", action="store_true", help="Instant run of the created test")

        # sec-audit
        p_sec = subparsers.add_parser("sec-audit", help="Security, injection and OWASP Top-10 vector audit")
        p_sec.add_argument("path", nargs="?", default="and_os", help="Path to scan (default: and_os)")

        # rules
        p_rules = subparsers.add_parser("rules", help="Compilation and audit of the rules fast index (Rules Fast Index)")
        p_rules.add_argument("action", nargs="?", choices=["compile", "audit", "verify", "diff"], default="compile", help="Action over the rules index")

    @classmethod
    def execute(cls, args: Any) -> int:
        cmd = args.command

        if cmd == "verify":
            flags = []
            if getattr(args, "json", False):
                flags.append("--json")
            if getattr(args, "verbose", False):
                flags.append("--verbose")
            if getattr(args, "paths", None):
                flags.extend(args.paths)
            res = run_script("quick_verify.py", flags)
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry("Quick pre-flight verification", skill="sys.verify")
            return res.get("returncode", 0)

        elif cmd == "audit":
            flags = []
            if getattr(args, "fix", False):
                flags.append("--fix")
            if getattr(args, "compact", False):
                flags.append("--compact")
            elif getattr(args, "json", False):
                flags.append("--json")

            res = run_script("validate_system.py", flags, no_bytecode=getattr(args, "read_only", False))
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            if not getattr(args, "read_only", False):
                auto_log_telemetry(f"Audit ({'fix' if getattr(args, 'fix', False) else 'check'})", skill="sys.audit")
            return res.get("returncode", 0)

        elif cmd == "eval":
            flags = [args.action]
            if getattr(args, "feature", None):
                flags.append(args.feature)
            if args.action == "define":
                if getattr(args, "desc", None):
                    flags.extend(["--desc", args.desc])
                if getattr(args, "domain", None):
                    flags.extend(["--domain", args.domain])
            res = run_script("eval_engine.py", flags)
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry(f"Eval action: {args.action}", skill="sys.eval")
            return res.get("returncode", 0)

        elif cmd == "tdd":
            flags = [args.file]
            if getattr(args, "out", None):
                flags.extend(["--out", args.out])
            if getattr(args, "run", False):
                flags.append("--run")
            res = run_script("tdd_scaffold.py", flags)
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry(f"TDD scaffold for {args.file}", skill="sys.tdd")
            return res.get("returncode", 0)

        elif cmd == "sec-audit":
            flags = [args.path]
            res = run_script("sec_audit.py", flags)
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry(f"Security audit for {args.path}", skill="sys.sec-audit")
            return res.get("returncode", 0)

        elif cmd == "rules":
            flags = [args.action] if getattr(args, "action", None) else ["compile"]
            res = run_script("rules_compiler.py", flags)
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry(f"Rules index action: {args.action}", skill="sys.rules")
            return res.get("returncode", 0)

        return 1
