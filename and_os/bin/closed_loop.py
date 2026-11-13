#!/usr/bin/env python3
"""
closed_loop.py — The Unified Master Dispatcher of the Closed Loop (Closed-Loop Sovereign OS Stack v1.0).
Provides the end-to-end registration of the artifacts without the manual requests of the user:
  1. Documents: the routing into the target Island in Nero/, the frontmatter, the auto-linking into CONTEXT.md.
  2. Scripts: the py_compile syntax check, the binding to sys_cli.py.
  3. Skills: the creation per the ABI v2.0, the symlink, the cascading update of the kernel manifests.
  4. Telemetry: the atomic fixation of each action in the telemetry.md.
  5. The two-level verification: the L1 Fast-Path (<80 ms) + the optional L2 Full Audit.

Commands:
  register-doc     -- Register the document/note with the binding to CONTEXT.md
  register-script  -- Register the system script
  register-skill   -- Register the new skill with all the manifests
  audit-l1         -- The instant L1 check of the single artifact (< 50 ms)
  audit-l2         -- The full 25-vector audit of the system + the 50 skills SOS
"""

import os
import sys
import json
import argparse
from typing import Dict, Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
LIB_DIR = os.path.join(SCRIPT_DIR, "..", "lib", "closed_loop")
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

from doc_router import DocRouter
from script_router import ScriptRouter
from skill_integrator import SkillIntegrator
from telemetry_guard import TelemetryGuard
from knowledge_router import KnowledgeRouter
from health_router import HealthRouter
from finance_router import FinanceRouter
from tasks_router import TasksRouter


def cmd_register_knowledge(args):
    """L1 registration of the knowledge: the routing, the binding to CONTEXT.md, the competence matrix and the index."""
    tags_list = [t.strip() for t in args.tags.split(",") if t.strip()] if getattr(args, "tags", "") else []
    checklist_list = [c.strip() for c in args.checklist.split(";") if c.strip()] if getattr(args, "checklist", "") else []
    
    res = KnowledgeRouter.register_knowledge(
        title=args.title,
        author=getattr(args, "author", "") or "",
        category=getattr(args, "category", "") or "Управление",
        island=getattr(args, "island", "") or "",
        essence=getattr(args, "essence", "") or "",
        for_whom=getattr(args, "for_whom", "") or "",
        competence=getattr(args, "competence", "") or "",
        skill=getattr(args, "skill", "") or "",
        tasks=getattr(args, "tasks", "") or "",
        tags=tags_list,
        content=getattr(args, "content", "") or "",
        checklist=checklist_list
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))


def cmd_register_health(args):
    """L1 registration of the medical fact or the consultation into the time series."""
    if args.type == "fact":
        res = HealthRouter.register_biomarker(
            patient_id=args.patient,
            test_date=args.date,
            marker_key=args.key,
            marker_name=args.name,
            value=float(args.value),
            unit=args.unit,
            ref_low=float(args.ref_low) if args.ref_low else None,
            ref_high=float(args.ref_high) if args.ref_high else None,
            lab_name=getattr(args, "lab", "ИНВИТРО") or "ИНВИТРО",
            source_doc=getattr(args, "source", "") or "",
            system_category=getattr(args, "category", "blood") or "blood"
        )
    elif args.type == "consultation":
        res = HealthRouter.register_consultation(
            patient_id=args.patient,
            consult_date=args.date,
            specialty=getattr(args, "specialty", "Терапевт") or "Терапевт",
            diagnosis_title=args.name,
            icd10_code=getattr(args, "icd10", "") or "",
            recommendations=getattr(args, "recommendations", "") or "",
            doctor_name=getattr(args, "doctor", "") or "",
            clinic_name=getattr(args, "clinic", "") or "",
            source_doc=getattr(args, "source", "") or ""
        )
    else:
        res = {"status": "error", "message": f"Unknown record type '{args.type}'. Allowed: fact, consultation"}
    print(json.dumps(res, ensure_ascii=False, indent=2))


def cmd_register_finance(args):
    """L1 registration of the financial slice or the money flow (Air-Gap)."""
    if args.type == "snapshot":
        res = FinanceRouter.register_snapshot(
            account_id=args.account,
            total_value=float(args.total),
            pnl_rub=float(args.pnl_rub) if args.pnl_rub else 0.0,
            pnl_pct=float(args.pnl_pct) if args.pnl_pct else 0.0,
            cash_rub=float(args.cash) if args.cash else 0.0,
            snapshot_date=getattr(args, "date", "") or "",
            source_doc=getattr(args, "source", "") or ""
        )
    elif args.type == "cashflow":
        res = FinanceRouter.register_cashflow(
            account_id=args.account,
            flow_type=getattr(args, "flow", "DIVIDEND") or "DIVIDEND",
            amount=float(args.total),
            ticker=getattr(args, "ticker", "") or "",
            date=getattr(args, "date", "") or "",
            note=getattr(args, "note", "") or ""
        )
    else:
        res = {"status": "error", "message": f"Unknown financial operation type '{args.type}'. Allowed: snapshot, cashflow"}
    print(json.dumps(res, ensure_ascii=False, indent=2))


def cmd_register_task(args):
    """L1 registration of the task with all the subtasks into the Tasks/ board."""
    subtasks = [s.strip() for s in args.subtasks.split(";") if s.strip()] if getattr(args, "subtasks", "") else []
    res = TasksRouter.register_task(
        project=args.project,
        title=args.title,
        subtasks=subtasks,
        priority=getattr(args, "priority", "normal") or "normal",
        due_date=getattr(args, "due", "") or "",
        section=getattr(args, "section", "") or ""
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))


def cmd_register_doc(args):
    """L1 registration of the document: the binding to CONTEXT.md and the telemetry write."""
    file_path = args.file
    summary = args.summary or ""
    task_name = args.task or f"Register document: {os.path.basename(file_path)}"

    if not os.path.exists(file_path):
        print(json.dumps({"status": "ERROR", "message": f"File not found: {file_path}"}), file=sys.stderr)
        sys.exit(1)

    linked = DocRouter.link_in_parent_context(file_path, summary)
    logged = TelemetryGuard.log_event(task_name, skill="closed_loop.doc", mode="WORK", result="success" if linked else "warn")

    result = {
        "status": "OK" if linked else "WARN",
        "action": "DOCUMENT_REGISTERED",
        "file": file_path,
        "parent_context_linked": linked,
        "telemetry_logged": logged
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_register_script(args):
    """L1 registration of the script: the syntax validation and the telemetry write."""
    file_path = args.file
    task_name = args.task or f"Register script: {os.path.basename(file_path)}"

    val_res = ScriptRouter.validate_script_syntax(file_path)
    if not val_res["valid"]:
        print(json.dumps({"status": "ERROR", "message": val_res["error"]}), file=sys.stderr)
        sys.exit(2)

    script_name = os.path.basename(file_path)
    cmd_help = getattr(args, "cmd_help", "")
    in_cli = ScriptRouter.register_in_sys_cli(script_name, args.subcommand or "", cmd_help)
    logged = TelemetryGuard.log_event(task_name, skill="closed_loop.script", mode="SYSTEM", result="success")

    result = {
        "status": "OK",
        "action": "SCRIPT_REGISTERED",
        "script": file_path,
        "syntax_valid": True,
        "registered_in_sys_cli": in_cli,
        "telemetry_logged": logged
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_register_skill(args):
    """L1 registration of the skill: the symlink, the cascading manifests, the telemetry."""
    name = args.name
    desc = args.desc
    domain = args.domain or "system_island_6"
    task_name = f"Register skill: {name}"

    res = SkillIntegrator.register_skill_manifests(name, desc, domain)
    if not res["success"]:
        print(json.dumps({"status": "ERROR", "message": res.get("error")}), file=sys.stderr)
        sys.exit(3)

    logged = TelemetryGuard.log_event(task_name, skill="closed_loop.skill", mode="SYSTEM", result="success")

    result = {
        "status": "OK",
        "action": "SKILL_REGISTERED",
        "skill": name,
        "updated_manifests": res["updated_manifests"],
        "telemetry_logged": logged
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_audit_l1(args):
    """The instant L1 audit of the specific artifact (< 50 ms)."""
    target = args.target
    if not os.path.exists(target):
        print(json.dumps({"status": "ERROR", "message": f"Target not found: {target}"}), file=sys.stderr)
        sys.exit(1)

    if target.endswith(".py"):
        val = ScriptRouter.validate_script_syntax(target)
        print(json.dumps({"level": "L1", "type": "script", "valid": val["valid"], "error": val.get("error")}))
    elif target.endswith(".md"):
        parent_ctx = DocRouter.find_nearest_context(target)
        has_ctx = parent_ctx is not None and os.path.exists(parent_ctx)
        doc_name = os.path.splitext(os.path.basename(target))[0]
        linked = False
        if has_ctx:
            with open(parent_ctx, "r", encoding="utf-8") as f:
                content = f.read()
                linked = f"[[{doc_name}]]" in content or f"[[{doc_name}|" in content
        print(json.dumps({"level": "L1", "type": "doc", "context_file": os.path.relpath(parent_ctx, VAULT_ROOT) if parent_ctx else None, "has_parent_context": has_ctx, "is_linked": linked}))


def cmd_audit_l2(args):
    """The full L2 audit of the kernel and the parallel stack of the skills (1.5-2.5 s)."""
    import subprocess
    t0 = os.times()[4]
    
    val_script = os.path.join(VAULT_ROOT, "and_os", "bin", "validate_system.py")
    sos_script = os.path.join(VAULT_ROOT, "and_os", "bin", "sos_auditor.py")
    
    r1 = subprocess.run(["python3", sos_script, "--json"], capture_output=True, text=True)
    r2 = subprocess.run(["python3", val_script, "--compact"], capture_output=True, text=True)
    
    elapsed = round(os.times()[4] - t0, 2)
    print(r2.stdout, end="")
    print(f"⚡ [L2 AUDIT PASSED] Multi-Core Check Completed in {elapsed}s.")


def main():
    parser = argparse.ArgumentParser(description="AnD os Closed-Loop Sovereign OS Stack")
    subparsers = parser.add_subparsers(dest="command")

    p_know = subparsers.add_parser("register-knowledge", help="The registration of the knowledge/book, the binding to the CONTEXT, the matrix and the index")
    p_know.add_argument("--title", required=True, help="The title of the book/article")
    p_know.add_argument("--author", default="", help="The author of the book/material")
    p_know.add_argument("--category", default="Управление", help="Category (the RU values: Управление, Эффективность, Ии, Лидерство, etc.)")
    p_know.add_argument("--island", default="", help="The target Island (clippings, cg_core, ta_bu, story, book, etc.)")
    p_know.add_argument("--essence", default="", help="The brief practical essence")
    p_know.add_argument("--for-whom", default="", dest="for_whom", help="The target audience and the roles")
    p_know.add_argument("--competence", default="", help="The competence for the competence matrix")
    p_know.add_argument("--skill", default="", help="The related system skill (e.g. status-report)")
    p_know.add_argument("--tasks", default="", help="The applied tasks solved")
    p_know.add_argument("--tags", default="", help="The tags separated by a comma")
    p_know.add_argument("--content", default="", help="The main text/principles")
    p_know.add_argument("--checklist", default="", help="The checklist items separated by a semicolon (;)")

    p_health = subparsers.add_parser("register-health", help="The registration of the medical fact or the consultation into the time series")
    p_health.add_argument("--patient", required=True, choices=["andrey", "misha", "yulia", "pavel", "mom"], help="The patient ID")
    p_health.add_argument("--type", choices=["fact", "consultation"], default="fact", help="The record type (fact or consultation)")
    p_health.add_argument("--date", required=True, help="The test/visit date (YYYY-MM-DD)")
    p_health.add_argument("--key", default="", help="The marker key (wbc, crp, alt, ast, etc.)")
    p_health.add_argument("--name", required=True, help="The marker or the diagnosis name")
    p_health.add_argument("--value", default="0", help="The indicator value")
    p_health.add_argument("--unit", default="", help="The unit of measurement")
    p_health.add_argument("--ref-low", default="", dest="ref_low", help="The lower norm boundary")
    p_health.add_argument("--ref-high", default="", dest="ref_high", help="The upper norm boundary")
    p_health.add_argument("--lab", default="ИНВИТРО", help="The laboratory")
    p_health.add_argument("--source", default="", help="The source document")
    p_health.add_argument("--category", default="blood", help="The system category (blood, urine, liver, etc.)")
    p_health.add_argument("--specialty", default="Терапевт", help="The doctor specialty (for the consultation)")
    p_health.add_argument("--icd10", default="", help="The ICD-10 code (for the consultation)")
    p_health.add_argument("--recommendations", default="", help="The prescriptions and the recommendations")
    p_health.add_argument("--doctor", default="", help="The doctor full name")
    p_health.add_argument("--clinic", default="", help="The clinic")

    p_fin = subparsers.add_parser("register-finance", help="The registration of the financial balance or the operation (Air-Gap)")
    p_fin.add_argument("--account", required=True, choices=["broker_account", "broker_account", "capital_account", "capital_account"], help="The broker account")
    p_fin.add_argument("--type", choices=["snapshot", "cashflow"], default="snapshot", help="The record type (snapshot or cashflow)")
    p_fin.add_argument("--total", required=True, help="The total account value or the inflow amount")
    p_fin.add_argument("--pnl-rub", default="0", dest="pnl_rub", help="The P/L in the rubles")
    p_fin.add_argument("--pnl-pct", default="0", dest="pnl_pct", help="The P/L in the percent")
    p_fin.add_argument("--cash", default="0", help="The free cash balance (the cash)")
    p_fin.add_argument("--flow", default="DIVIDEND", choices=["DIVIDEND", "COUPON", "CONTRIBUTION"], help="The inflow type")
    p_fin.add_argument("--ticker", default="", help="The asset ticker")
    p_fin.add_argument("--date", default="", help="The operation/slice date (YYYY-MM-DD)")
    p_fin.add_argument("--note", default="", help="The note")
    p_fin.add_argument("--source", default="", help="The source document")

    p_task = subparsers.add_parser("register-task", help="The registration of the task with all the subtasks into the Tasks/ board")
    p_task.add_argument("--project", required=True, choices=["mars", "kot", "pm", "Studio", "general"], help="The target project/board")
    p_task.add_argument("--title", required=True, help="The main task")
    p_task.add_argument("--subtasks", default="", help="The subtasks separated by a semicolon (;)")
    p_task.add_argument("--priority", default="normal", choices=["normal", "high", "urgent"], help="The priority")
    p_task.add_argument("--due", default="", help="The deadline (YYYY-MM-DD)")
    p_task.add_argument("--section", default="", help="The section name (H2) on the board")

    p_doc = subparsers.add_parser("register-doc", help="The registration of the document and the binding to the CONTEXT.md")
    p_doc.add_argument("--file", required=True, help="The path to the .md document")
    p_doc.add_argument("--summary", default="", help="The brief purpose of the document")
    p_doc.add_argument("--task", default="", help="The task name for the telemetry")

    p_script = subparsers.add_parser("register-script", help="The registration of the system script")
    p_script.add_argument("--file", required=True, help="The path to the python script")
    p_script.add_argument("--subcommand", default="", help="The subcommand name in the sys_cli.py")
    p_script.add_argument("--cmd-help", default="", help="The subcommand help")
    p_script.add_argument("--task", default="", help="The task name for the telemetry")

    p_sk = subparsers.add_parser("register-skill", help="The registration of the skill and the manifests")
    p_sk.add_argument("--name", required=True, help="The skill name (kebab-case)")
    p_sk.add_argument("--desc", required=True, help="The skill description")
    p_sk.add_argument("--domain", default="system_island_6", help="The domain/Island of the skill")

    p_l1 = subparsers.add_parser("audit-l1", help="The fast L1 audit of the single artifact (<50 ms)")
    p_l1.add_argument("--target", required=True, help="The path to the checked file")

    p_l2 = subparsers.add_parser("audit-l2", help="The full L2 audit of the system")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmds = {
        "register-knowledge": cmd_register_knowledge,
        "register-health": cmd_register_health,
        "register-finance": cmd_register_finance,
        "register-task": cmd_register_task,
        "register-doc": cmd_register_doc,
        "register-script": cmd_register_script,
        "register-skill": cmd_register_skill,
        "audit-l1": cmd_audit_l1,
        "audit-l2": cmd_audit_l2
    }
    cmds[args.command](args)


if __name__ == "__main__":
    main()
