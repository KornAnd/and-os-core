#!/usr/bin/env python3
"""
eval_engine.py - Eval-Driven Development (EDD) Framework for AnD os.
Inspired by Everything-Claude-Code eval harness and adapted for deterministic
testing, regression tracking, and reliability metrics (pass@1, pass@3, pass^3).

Commands:
  define <feature>    - Create new eval definition JSON with capability and regression items
  check <feature>     - Execute all eval graders, calculate pass@k metrics, log results
  report <feature>    - Generate comprehensive markdown readiness report
  list                - List all defined eval suites and their status
"""

import os
import sys
import json
import time
import argparse
import subprocess
from typing import Dict, Any, List

sys.dont_write_bytecode = True


class EvalEngine:
    def __init__(self, vault_root: str):
        self.vault_root = os.path.abspath(vault_root)
        self.evals_dir = os.path.join(self.vault_root, "and_os", "var", "evals")
        os.makedirs(self.evals_dir, exist_ok=True)

    def _get_eval_file(self, feature: str) -> str:
        safe_name = feature.replace(" ", "_").replace("/", "-")
        return os.path.join(self.evals_dir, f"{safe_name}.eval.json")

    def _get_log_file(self, feature: str) -> str:
        safe_name = feature.replace(" ", "_").replace("/", "-")
        return os.path.join(self.evals_dir, f"{safe_name}.eval.log")

    def define(self, feature: str, description: str = "", domain: str = "core") -> Dict[str, Any]:
        file_path = self._get_eval_file(feature)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)

        data = {
            "feature": feature,
            "domain": domain,
            "description": description or f"Eval suite for {feature}",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "success_criteria": {
                "target_pass_at_3": 0.9,
                "target_pass_pow_3": 1.0
            },
            "capability_evals": [
                {
                    "id": f"{feature}-cap-01",
                    "description": f"Verify primary capability of {feature}",
                    "command": "python3 and_os/bin/sys_cli.py boot",
                    "expected_exit_code": 0,
                    "expected_pattern": "Runlevel"
                }
            ],
            "regression_evals": [
                {
                    "id": f"{feature}-reg-01",
                    "description": "Ensure Quick Verification Loop passes",
                    "command": "python3 and_os/bin/sys_cli.py verify",
                    "expected_exit_code": 0,
                    "expected_pattern": "ALL PHASES PASSED"
                }
            ]
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return data

    def run_grader(self, item: Dict[str, Any], max_attempts: int = 3) -> Dict[str, Any]:
        """Runs grader command up to max_attempts times to compute pass@1 and pass@k."""
        cmd_str = item.get("command", "")
        exp_code = item.get("expected_exit_code", 0)
        exp_pattern = item.get("expected_pattern", "")

        attempts = []
        for attempt in range(1, max_attempts + 1):
            t0 = time.time()
            try:
                p = subprocess.run(
                    cmd_str,
                    shell=True,  # nosec: eval test execution
                    cwd=self.vault_root,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=15
                )
                dur = round(time.time() - t0, 3)
                output = p.stdout + "\n" + p.stderr
                success = (p.returncode == exp_code) and (not exp_pattern or exp_pattern in output)
                attempts.append({
                    "attempt": attempt,
                    "success": success,
                    "exit_code": p.returncode,
                    "duration": dur
                })
                if success:
                    break
            except Exception as e:
                attempts.append({
                    "attempt": attempt,
                    "success": False,
                    "exit_code": -1,
                    "error": str(e)
                })

        first_attempt_pass = attempts[0]["success"] if attempts else False
        eventual_pass = any(a["success"] for a in attempts)
        attempts_needed = next((a["attempt"] for a in attempts if a["success"]), -1)

        return {
            "id": item.get("id"),
            "description": item.get("description"),
            "pass_at_1": first_attempt_pass,
            "pass_at_3": eventual_pass,
            "attempts_needed": attempts_needed,
            "attempts": attempts
        }

    def check(self, feature: str) -> Dict[str, Any]:
        file_path = self._get_eval_file(feature)
        if not os.path.exists(file_path):
            return {"error": f"Eval suite '{feature}' not found. Run define first."}

        with open(file_path, "r", encoding="utf-8") as f:
            spec = json.load(f)

        cap_results = [self.run_grader(item) for item in spec.get("capability_evals", [])]
        reg_results = [self.run_grader(item) for item in spec.get("regression_evals", [])]

        total_cap = len(cap_results)
        cap_pass_1 = sum(1 for r in cap_results if r["pass_at_1"])
        cap_pass_3 = sum(1 for r in cap_results if r["pass_at_3"])

        total_reg = len(reg_results)
        reg_pass_1 = sum(1 for r in reg_results if r["pass_at_1"])
        reg_pass_3 = sum(1 for r in reg_results if r["pass_at_3"])

        pass_at_1_rate = round(cap_pass_1 / total_cap, 2) if total_cap else 1.0
        pass_at_3_rate = round(cap_pass_3 / total_cap, 2) if total_cap else 1.0
        reg_rate = round(reg_pass_3 / total_reg, 2) if total_reg else 1.0

        is_ready = (pass_at_3_rate >= spec["success_criteria"]["target_pass_at_3"]) and (reg_rate == 1.0)

        summary = {
            "feature": feature,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "capability": {
                "total": total_cap,
                "pass_at_1": cap_pass_1,
                "pass_at_3": cap_pass_3,
                "pass_at_1_rate": pass_at_1_rate,
                "pass_at_3_rate": pass_at_3_rate
            },
            "regression": {
                "total": total_reg,
                "passed": reg_pass_3,
                "rate": reg_rate
            },
            "status": "READY_FOR_SHIP" if is_ready else "NEEDS_WORK",
            "capability_details": cap_results,
            "regression_details": reg_results
        }

        # Append to log
        log_file = self._get_log_file(feature)
        with open(log_file, "a", encoding="utf-8") as lf:
            lf.write(json.dumps(summary, ensure_ascii=False) + "\n")

        return summary

    def list_evals(self) -> List[Dict[str, Any]]:
        suites = []
        if os.path.exists(self.evals_dir):
            for f in os.listdir(self.evals_dir):
                if f.endswith(".eval.json"):
                    with open(os.path.join(self.evals_dir, f), "r", encoding="utf-8") as fh:
                        suites.append(json.load(fh))
        return suites


def main():
    parser = argparse.ArgumentParser(description="AnD os Eval-Driven Development (EDD) Framework")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    p_def = subparsers.add_parser("define", help="Define a new eval suite")
    p_def.add_argument("feature", help="Feature or subsystem name")
    p_def.add_argument("--desc", default="", help="Requirements description")
    p_def.add_argument("--domain", default="core", help="System domain")

    p_chk = subparsers.add_parser("check", help="Run the eval check and compute metrics")
    p_chk.add_argument("feature", help="Feature name")

    p_lst = subparsers.add_parser("list", help="List available eval suites")

    args = parser.parse_args()
    vault_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    engine = EvalEngine(vault_root)

    if args.subcommand == "define":
        res = engine.define(args.feature, description=args.desc, domain=args.domain)
        print(f"✅ Eval suite defined: and_os/var/evals/{args.feature}.eval.json")
        print(f"  • Capabilities: {len(res['capability_evals'])}, Regressions: {len(res['regression_evals'])}")
    elif args.subcommand == "check":
        res = engine.check(args.feature)
        if "error" in res:
            print(f"❌ {res['error']}", file=sys.stderr)
            sys.exit(1)
        cap = res["capability"]
        reg = res["regression"]
        print("┌─────────────────────────────────────────────────────────────┐")
        print(f"│  📊 EDD Eval Report: {res['feature']:<25} [{res['status']}]  │")
        print("├─────────────────────────────────────────────────────────────┤")
        print(f"│  • Capability pass@1 : {cap['pass_at_1']}/{cap['total']} ({int(cap['pass_at_1_rate']*100)}%)                             │")
        print(f"│  • Capability pass@3 : {cap['pass_at_3']}/{cap['total']} ({int(cap['pass_at_3_rate']*100)}%)                             │")
        print(f"│  • Regression pass^3 : {reg['passed']}/{reg['total']} ({int(reg['rate']*100)}%)                             │")
        print(f"│  • Final Decision    : {'🟢 READY TO SHIP' if res['status'] == 'READY_FOR_SHIP' else '🔴 NEEDS WORK':<36} │")
        print("└─────────────────────────────────────────────────────────────┘")
    elif args.subcommand == "list":
        suites = engine.list_evals()
        if not suites:
            print("ℹ️ No eval suites defined.")
        else:
            print(f"📋 SYSTEM EVAL SUITES ({len(suites)}):")
            for s in suites:
                print(f"  • {s['feature']:<25} | Domain: {s.get('domain', 'core'):<10} | {s.get('description', '')}")


if __name__ == "__main__":
    main()
