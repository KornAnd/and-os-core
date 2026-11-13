#!/usr/bin/env python3
"""
post_prompt_planner.py — Automatic generator of process maps (Post-Prompt Execution Map / DAG Planner).
Principle: Think in Code (Rule #16), Task Execution Graph (Rule #20).

Purpose:
  Takes the text of a complex task (--task "...") and instantly generates a decomposed
  process map (DAG) with the primary skill assignment, CLI modules, input/output artifacts and DoD criteria.

Usage:
  python3 post_prompt_planner.py --task "Ftrack analytics for Mars and CG_core content preparation"
  python3 post_prompt_planner.py --task "..." --json
"""

import sys
import json
import argparse
from datetime import datetime

DOMAIN_MAP = [
    {"kw": ["ftrack", "марс", "кот", "производство", "шот"], "domain": "work", "primary": "status-report", "script": "ftrack_report.py --summary"},
    {"kw": ["здоровье", "анализ", "узи", "врач", "лекарство"], "domain": "health", "primary": "health-diagnostics-hub", "script": "pdf_twin_converter.py"},
    {"kw": ["статья", "пост", "vk", "linkedin", "cg_core"], "domain": "content", "primary": "cg-content-factory", "script": "sys_cli.py sync"},
    {"kw": ["бюджет", "смета", "ставка", "смена"], "domain": "finance", "primary": "budget-calculator", "script": "budget_calc.py"},
    {"kw": ["аудит", "система", "целостность", "контекст"], "domain": "system", "primary": "system-audit", "script": "sys_cli.py audit"},
    {"kw": ["задача", "дедлайн", "спринт", "weeek"], "domain": "tasks", "primary": "weeek-hub", "script": "task_db_engine.py --index"}
]

def generate_execution_plan(task_text):
    text_low = task_text.lower()
    matched_steps = []
    step_num = 1

    # Step 1: Retrieval & Quick State
    matched_steps.append({
        "step": step_num,
        "name": "Quick Retrieval & Domain State Check",
        "primary_skill": "sys_cli",
        "script": "sys_cli.py state --get-all",
        "inputs": ["Clippings/quick_knowledge_db.json", "domain_states.json"],
        "outputs": ["Quick Context Summary"],
        "dod": "Context extracted without reading extra files"
    })
    step_num += 1

    # Step 2: Domain-specific execution steps
    for item in DOMAIN_MAP:
        for k in item["kw"]:
            if k in text_low:
                matched_steps.append({
                    "step": step_num,
                    "name": f"Execution Phase: {item['domain'].capitalize()} Processing",
                    "primary_skill": item["primary"],
                    "script": item["script"],
                    "inputs": [f"{item['domain']} raw data"],
                    "outputs": [f"Processed {item['domain']} artifact"],
                    "dod": f"Stage {item['domain']} completed with a DoD confirmation"
                })
                step_num += 1
                break

    # Step 3: Verification & Memory
    matched_steps.append({
        "step": step_num,
        "name": "System Audit & Telemetry Logging",
        "primary_skill": "sys_cli",
        "script": "sys_cli.py audit",
        "inputs": ["Generated Artifacts"],
        "outputs": ["and_os/lib/skills/telemetry.md"],
        "dod": "13 audit vectors passed, telemetry recorded"
    })

    plan = {
        "status": "SUCCESS",
        "task_name": task_text,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_steps": len(matched_steps),
        "execution_dag": matched_steps
    }
    return plan

def main():
    parser = argparse.ArgumentParser(description="Post-Prompt Execution Map Generator")
    parser.add_argument("--task", type=str, required=True, help="Text of the incoming task")
    parser.add_argument("--json", action="store_true", help="JSON format output")

    args = parser.parse_args()
    plan = generate_execution_plan(args.task)

    if args.json:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    else:
        print(f"\n🗺️  TARGET PROCESS MAP (Post-Prompt Execution DAG)")
        print(f"📋 Task: {plan['task_name']}")
        print(f"⏱️  Created: {plan['created_at']} | Total stages: {plan['total_steps']}\n" + "-" * 65)

        for s in plan["execution_dag"]:
            print(f"Step {s['step']}: {s['name']}")
            print(f"  ├─ Primary Skill: {s['primary_skill']}")
            print(f"  ├─ CLI Script   : {s['script']}")
            print(f"  ├─ In / Out     : {', '.join(s['inputs'])}  ➔  {', '.join(s['outputs'])}")
            print(f"  └─ DoD Criterion: {s['dod']}\n")

if __name__ == "__main__":
    main()
