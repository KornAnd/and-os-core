#!/usr/bin/env python3
"""
dev_flow.py — Modular CLI orchestrator for strict step-by-step development in AnD os.
Manages the development session via a deterministic FSM and a temporary .dev_session.json.

Commands:
  init         -- Initialize the task session
  lock-spec    -- Freeze spec invariants (goal, prohibitions, acceptance)
  plan         -- Load and validate the phase DAG
  step-begin   -- Start step execution (creates a snapshot for rollback)
  step-verify  -- Run the step test/check (Circuit Breaker Stop-on-3 protection)
  step-finish  -- Finish the step and move to the next
  rollback     -- Immediate rollback of the current step's files from the snapshot
  status       -- Show the current session state
  finish       -- Complete the task and generate an honest DEV_PROTOCOL report
"""

import sys
import os
import sys
from pathlib import Path
_vroot = str(Path(__file__).resolve().parents[2])
if _vroot not in sys.path:
    sys.path.insert(0, _vroot)
from and_os.lib.core.vault_safe_io import vault_safe_write

import json
import argparse
from typing import Dict, Any, List

# Module imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AND_OS_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DEV_FLOW_LIB = os.path.join(AND_OS_ROOT, "lib", "dev_flow")
if DEV_FLOW_LIB not in sys.path:
    sys.path.insert(0, DEV_FLOW_LIB)

from contract_guard import ContractGuard
from dag_engine import DAGEngine
from isolation_guard import IsolationGuard
from verifier import Verifier
from report_generator import ReportGenerator

DEFAULT_SESSION_FILE = ".dev_session.json"
SNAPSHOT_DIR = os.path.join(".dev_snapshots")


def load_session(path: str = DEFAULT_SESSION_FILE) -> Dict[str, Any]:
    if not os.path.exists(path):
        print(f"[ERROR] Dev session file not found: {path}. Run 'init' first.", file=sys.stderr)
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_session(session: Dict[str, Any], path: str = DEFAULT_SESSION_FILE):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session, f, ensure_ascii=False, indent=2)


def cmd_init(args):
    session = {
        "session_id": f"dev_{int(os.times()[4] * 1000)}",
        "task": args.task,
        "state": "INIT",
        "invariants": {},
        "circuit_breaker": {
            "max_retries": 3,
            "current_step_retries": 0,
            "total_failures": 0
        },
        "snapshot_map": {},
        "dag": [],
        "current_step_id": None,
        "verification_log": [],
        "unverified_items": []
    }
    save_session(session)
    print(json.dumps({"status": "OK", "state": "INIT", "session_id": session["session_id"]}))


def cmd_lock_spec(args):
    session = load_session()
    invariants = {
        "goal": args.goal,
        "forbidden": args.forbidden if isinstance(args.forbidden, list) else [x.strip() for x in args.forbidden.split(";")],
        "acceptance_criteria": args.acceptance
    }
    errors = ContractGuard.validate_invariants(invariants)
    if errors:
        print(json.dumps({"status": "ERROR", "errors": errors}), file=sys.stderr)
        sys.exit(2)
        
    session["invariants"] = invariants
    session["state"] = "SPEC_LOCKED"
    save_session(session)
    print(json.dumps({"status": "OK", "state": "SPEC_LOCKED", "invariants": invariants}))


def cmd_plan(args):
    session = load_session()
    if session.get("state") not in ["SPEC_LOCKED", "PLAN_READY"]:
        print(json.dumps({"status": "ERROR", "message": "Spec must be locked before planning!"}), file=sys.stderr)
        sys.exit(2)
        
    with open(args.file, "r", encoding="utf-8") as f:
        steps = json.load(f)
        
    errors = DAGEngine.validate_dag(steps)
    if errors:
        print(json.dumps({"status": "ERROR", "errors": errors}), file=sys.stderr)
        sys.exit(2)
        
    parallel_analysis = DAGEngine.analyze_parallel_safety(steps)
    
    # Initialize steps state
    for s in steps:
        s["status"] = "PENDING"
        s["attempts"] = 0
        
    session["dag"] = steps
    session["state"] = "PLAN_READY"
    session["parallel_safety"] = parallel_analysis
    save_session(session)
    print(json.dumps({
        "status": "OK",
        "state": "PLAN_READY",
        "total_steps": len(steps),
        "parallel_safety": parallel_analysis
    }))


def cmd_step_begin(args):
    session = load_session()
    sid = args.id
    target_step = next((s for s in session.get("dag", []) if s["id"] == sid), None)
    if not target_step:
        print(json.dumps({"status": "ERROR", "message": f"Step ID '{sid}' not found in DAG"}), file=sys.stderr)
        sys.exit(2)
        
    # Create file snapshot before edits
    target_files = target_step.get("target_files", [])
    backup_map = IsolationGuard.create_snapshot(os.getcwd(), target_files, SNAPSHOT_DIR)
    
    session["current_step_id"] = sid
    session["snapshot_map"] = backup_map
    session["circuit_breaker"]["current_step_retries"] = target_step.get("attempts", 0)
    target_step["status"] = "IN_PROGRESS"
    session["state"] = "STEP_IN_PROGRESS"
    
    save_session(session)
    print(json.dumps({
        "status": "OK",
        "state": "STEP_IN_PROGRESS",
        "current_step": sid,
        "backed_up_files": list(backup_map.keys())
    }))


def cmd_step_verify(args):
    session = load_session()
    sid = session.get("current_step_id")
    if not sid:
        print(json.dumps({"status": "ERROR", "message": "No active step in progress!"}), file=sys.stderr)
        sys.exit(2)
        
    target_step = next((s for s in session.get("dag", []) if s["id"] == sid), None)
    target_step["attempts"] = target_step.get("attempts", 0) + 1
    session["circuit_breaker"]["current_step_retries"] = target_step["attempts"]
    
    # Check circuit breaker limit
    if Verifier.check_circuit_breaker(target_step["attempts"]):
        session["circuit_breaker"]["total_failures"] += 1
        session["state"] = "CIRCUIT_BREAKER_TRIGGERED"
        # Automatic rollback upon circuit breaker
        restored = IsolationGuard.rollback(session.get("snapshot_map", {}))
        save_session(session)
        print(json.dumps({
            "status": "CIRCUIT_BREAKER_TRIGGERED",
            "message": f"Hard Stop-on-3 reached for step '{sid}'! Files automatically restored.",
            "restored_files": restored,
            "attempts": target_step["attempts"]
        }), file=sys.stderr)
        sys.exit(42)
        
    # Execute verification
    cmd = args.cmd or target_step.get("verify_cmd")
    res = Verifier.execute_verification(cmd, os.getcwd())
    
    log_entry = {
        "step_id": sid,
        "cmd": cmd,
        "exit_code": res["exit_code"],
        "duration_sec": res["duration_sec"],
        "success": res["success"]
    }
    session["verification_log"].append(log_entry)
    
    if not res["success"]:
        save_session(session)
        print(json.dumps({
            "status": "STEP_VERIFY_FAILED",
            "step_id": sid,
            "attempts": target_step["attempts"],
            "remaining_retries": 3 - target_step["attempts"],
            "stderr": res["stderr"]
        }))
        sys.exit(3)
        
    save_session(session)
    print(json.dumps({
        "status": "STEP_VERIFY_SUCCESS",
        "step_id": sid,
        "duration_sec": res["duration_sec"],
        "exit_code": res["exit_code"]
    }))


def cmd_step_finish(args):
    session = load_session()
    sid = session.get("current_step_id")
    if not sid:
        print(json.dumps({"status": "ERROR", "message": "No active step to finish!"}), file=sys.stderr)
        sys.exit(2)
        
    target_step = next((s for s in session.get("dag", []) if s["id"] == sid), None)
    target_step["status"] = "COMPLETED"
    session["current_step_id"] = None
    session["snapshot_map"] = {}
    session["circuit_breaker"]["current_step_retries"] = 0
    
    # Check if all completed
    all_done = all(s.get("status") == "COMPLETED" for s in session.get("dag", []))
    session["state"] = "ALL_STEPS_COMPLETED" if all_done else "STEP_COMPLETED"
    
    save_session(session)
    print(json.dumps({
        "status": "OK",
        "state": session["state"],
        "finished_step": sid,
        "all_completed": all_done
    }))


def cmd_rollback(args):
    session = load_session()
    backup_map = session.get("snapshot_map", {})
    restored = IsolationGuard.rollback(backup_map)
    session["state"] = "ROLLED_BACK"
    save_session(session)
    print(json.dumps({
        "status": "OK",
        "state": "ROLLED_BACK",
        "restored_files": restored
    }))


def cmd_finish(args):
    session = load_session()
    if args.unverified:
        items = [x.strip() for x in args.unverified.split(";")]
        session["unverified_items"] = items
        
    report = ReportGenerator.generate_markdown_report(session)
    session["state"] = "FINISHED"
    save_session(session)
    
    report_file = args.report_file or "DEV_REPORT.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(json.dumps({
        "status": "OK",
        "state": "FINISHED",
        "report_file": report_file
    }))


def cmd_status(args):
    session = load_session()
    print(json.dumps(session, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="AnD os Modular Dev Flow Engine")
    subparsers = parser.add_subparsers(dest="command")

    p_init = subparsers.add_parser("init")
    p_init.add_argument("--task", required=True, help="Title/description of the task")

    p_spec = subparsers.add_parser("lock-spec")
    p_spec.add_argument("--goal", required=True, help="Strict objective of the task")
    p_spec.add_argument("--forbidden", required=True, help="Forbidden actions / sensitive systems (semicolon separated)")
    p_spec.add_argument("--acceptance", required=True, help="Exact acceptance criteria (DoD)")

    p_plan = subparsers.add_parser("plan")
    p_plan.add_argument("--file", required=True, help="Path to JSON file containing DAG steps")

    p_begin = subparsers.add_parser("step-begin")
    p_begin.add_argument("--id", required=True, help="Step ID to begin")

    p_verify = subparsers.add_parser("step-verify")
    p_verify.add_argument("--cmd", required=False, help="Custom verification command (optional, defaults to step.verify_cmd)")

    p_finish_step = subparsers.add_parser("step-finish")

    p_rollback = subparsers.add_parser("rollback")

    p_finish = subparsers.add_parser("finish")
    p_finish.add_argument("--unverified", required=False, help="Semicolon separated list of unverified physical items")
    p_finish.add_argument("--report-file", required=False, default="DEV_REPORT.md")

    p_status = subparsers.add_parser("status")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmds = {
        "init": cmd_init,
        "lock-spec": cmd_lock_spec,
        "plan": cmd_plan,
        "step-begin": cmd_step_begin,
        "step-verify": cmd_step_verify,
        "step-finish": cmd_step_finish,
        "rollback": cmd_rollback,
        "finish": cmd_finish,
        "status": cmd_status
    }
    cmds[args.command](args)


if __name__ == "__main__":
    main()
