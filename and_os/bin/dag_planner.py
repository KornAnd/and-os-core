#!/usr/bin/env python3
"""
dag_planner.py - DAG Phase Planner & Acceptance Criteria Engine for AnD os.
Enforces Rule #20 and Rule #36 (Atomic Phased Execution & DoD Checkpoints).
Manages structured phased task plans in `and_os/var/plans/<task>.plan.json`.
"""

import sys
import os
import json
import time
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

VAULT_ROOT = Path(__file__).resolve().parent.parent.parent
PLANS_DIR = VAULT_ROOT / "and_os" / "var" / "plans"

def ensure_plans_dir():
    PLANS_DIR.mkdir(parents=True, exist_ok=True)

def new_plan(task_id: str, phases_str: str, desc: str = "") -> Dict[str, Any]:
    ensure_plans_dir()
    plan_file = PLANS_DIR / f"{task_id}.plan.json"
    
    phase_names = [p.strip() for p in phases_str.split(",") if p.strip()]
    if not phase_names:
        phase_names = ["1. Architecture & Design", "2. Implementation", "3. Testing & Verification", "4. Acceptance & Review"]

    phases = []
    for idx, name in enumerate(phase_names, 1):
        phases.append({
            "id": f"phase_{idx}",
            "name": name,
            "status": "IN_PROGRESS" if idx == 1 else "PENDING",
            "acceptance_criteria": [
                f"Contract verification for {name}",
                "DoD verification passed"
            ],
            "completed_criteria": [],
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z") if idx == 1 else None,
            "completed_at": None
        })

    plan = {
        "task_id": task_id,
        "description": desc or f"Execution DAG Plan for {task_id}",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "current_phase_index": 0,
        "status": "ACTIVE",
        "phases": phases
    }

    with open(plan_file, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)

    return plan

def load_plan(task_id: str) -> Optional[Dict[str, Any]]:
    plan_file = PLANS_DIR / f"{task_id}.plan.json"
    if not plan_file.exists():
        return None
    try:
        with open(plan_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def save_plan(task_id: str, plan: Dict[str, Any]):
    ensure_plans_dir()
    plan_file = PLANS_DIR / f"{task_id}.plan.json"
    with open(plan_file, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)

def check_phase(task_id: str, mark_done: bool = False) -> Dict[str, Any]:
    plan = load_plan(task_id)
    if not plan:
        return {"error": f"Plan '{task_id}' not found."}

    curr_idx = plan.get("current_phase_index", 0)
    phases = plan.get("phases", [])
    if curr_idx >= len(phases):
        return {"status": "ALL_COMPLETED", "message": "All phases are completed!"}

    curr_phase = phases[curr_idx]
    
    if mark_done:
        curr_phase["status"] = "COMPLETED"
        curr_phase["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        curr_phase["completed_criteria"] = list(curr_phase["acceptance_criteria"])
        
        # Advance to next phase
        next_idx = curr_idx + 1
        plan["current_phase_index"] = next_idx
        if next_idx < len(phases):
            phases[next_idx]["status"] = "IN_PROGRESS"
            phases[next_idx]["started_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        else:
            plan["status"] = "COMPLETED"
            
        save_plan(task_id, plan)
        return {
            "status": "ADVANCED",
            "completed_phase": curr_phase["name"],
            "next_phase": phases[next_idx]["name"] if next_idx < len(phases) else "None (Done)",
            "all_done": next_idx >= len(phases)
        }

    return {
        "status": "CURRENT_PHASE",
        "phase_id": curr_phase["id"],
        "name": curr_phase["name"],
        "phase_status": curr_phase["status"],
        "criteria": curr_phase["acceptance_criteria"],
        "started_at": curr_phase.get("started_at")
    }

def print_status(task_id: Optional[str] = None):
    ensure_plans_dir()
    if task_id:
        plan = load_plan(task_id)
        if not plan:
            print(f"❌ Plan '{task_id}' not found.")
            return
        
        print(f"📋 Task Plan: {plan['task_id']} [{plan['status']}]")
        print(f"   Desc: {plan.get('description', '')}")
        print("-" * 60)
        for idx, p in enumerate(plan.get("phases", [])):
            icon = "🟢" if p["status"] == "COMPLETED" else ("🟡" if p["status"] == "IN_PROGRESS" else "⚪")
            curr_mark = " ◀ CURRENT" if idx == plan.get("current_phase_index", 0) and plan["status"] != "COMPLETED" else ""
            print(f" {icon} Phase {idx + 1}: {p['name']} [{p['status']}]{curr_mark}")
            for c in p.get("acceptance_criteria", []):
                done_icon = "✓" if c in p.get("completed_criteria", []) else "○"
                print(f"      {done_icon} {c}")
        print("-" * 60)
    else:
        plans = sorted(PLANS_DIR.glob("*.plan.json"))
        if not plans:
            print("ℹ️ No active task plans in and_os/var/plans/.")
            return
        print("📋 Active DAG Plans:")
        for p_file in plans:
            try:
                with open(p_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                status_icon = "🟢" if data.get("status") == "COMPLETED" else "🟡"
                curr_idx = data.get("current_phase_index", 0)
                total = len(data.get("phases", []))
                print(f" {status_icon} {data.get('task_id', p_file.stem):24} | Phase: {curr_idx + 1}/{total} | Status: {data.get('status')}")
            except Exception:
                pass

def main():
    parser = argparse.ArgumentParser(description="DAG Phase Planner & Acceptance Criteria Engine")
    subparsers = parser.add_subparsers(dest="action")

    p_new = subparsers.add_parser("new", help="Create a new task plan")
    p_new.add_argument("task_id", help="Unique task identifier")
    p_new.add_argument("--phases", "-p", default="", help="Comma-separated list of phase names")
    p_new.add_argument("--desc", "-d", default="", help="Task description")

    p_check = subparsers.add_parser("check", help="Check current phase or mark it done")
    p_check.add_argument("task_id", help="Unique task identifier")
    p_check.add_argument("--done", action="store_true", help="Mark current phase completed and advance")

    p_status = subparsers.add_parser("status", help="Show status of plans")
    p_status.add_argument("task_id", nargs="?", help="Specific task ID to display")

    args = parser.parse_args()

    if args.action == "new":
        plan = new_plan(args.task_id, args.phases, desc=args.desc)
        print(f"✅ Created plan '{args.task_id}' with {len(plan['phases'])} phases in and_os/var/plans/{args.task_id}.plan.json")
    elif args.action == "check":
        res = check_phase(args.task_id, mark_done=args.done)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.action == "status" or not args.action:
        print_status(getattr(args, "task_id", None))

if __name__ == "__main__":
    main()
