#!/usr/bin/env python3
"""
Component Lifecycle & Registration Engine (register_component.py)
AnD os v1.0.0 - Modular Architecture Infrastructure

The automated tool for the safe addition, the update and the registration:
1. The New Skills (and_os/lib/skills/<name>/SKILL.md -> the symlink .opencode/skills/ -> CONTEXT.md -> ROUTING.md)
2. The New Scripts/Modules into the Hubs (and_os/opt/apps/<hub>/modules/ -> modules_registry.json -> <hub>_cli.py)

Provides the 100% consistency of the metadata, the syntax validation and the passing of all the gates.
"""

import os
import sys
from pathlib import Path
_vroot = str(Path(__file__).resolve().parents[2])
if _vroot not in sys.path:
    sys.path.insert(0, _vroot)
from and_os.lib.core.vault_safe_io import vault_safe_write

import sys
import json
import argparse
import subprocess
import datetime
import py_compile

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SKILLS_DIR = os.path.join(VAULT_ROOT, "and_os", "lib", "skills")
OPENCODE_SKILLS_DIR = os.path.join(VAULT_ROOT, ".opencode", "skills")
APPS_DIR = os.path.join(VAULT_ROOT, "and_os", "opt", "apps")

def register_skill(name: str, desc: str, domain: str = "General", tags: list = None) -> dict:
    """Creates the template of the new skill, registers the symlink and updates the registries."""
    skill_dir = os.path.join(SKILLS_DIR, name)
    skill_file = os.path.join(skill_dir, "SKILL.md")
    
    if os.path.exists(skill_dir):
        return {"status": "error", "message": f"The skill {name} already exists in the {skill_dir}"}
        
    os.makedirs(skill_dir, exist_ok=True)
    tags_list = tags or ["nero", "skills", name]
    yaml_tags = "\n".join([f"  - {t}" for t in tags_list])
    
    skill_template = f"""---
tags:
{yaml_tags}
name: {name}
description: "{desc}"
domain: {domain}
lifecycle: ACTIVE
version: 1.0.0
created: {datetime.datetime.now().strftime('%d.%m.%Y')}
---

# {name}

## Purpose
{desc}

## The Input Data
- Describe the input parameters or the files.

## The Algorithm
1. Step 1: The initialization and the validation.
2. Step 2: The execution of the target action.
3. Step 3: The saving of the artifacts and the report.

## The Output Artifact
- Describe the result of the work (Markdown, JSON, file).

---
[[CONTEXT|Back to the list of the skills]]
"""
    with open(skill_file, "w", encoding="utf-8") as f:
        f.write(skill_template)
        
    # The creation of the symlink
    os.makedirs(OPENCODE_SKILLS_DIR, exist_ok=True)
    symlink_path = os.path.join(OPENCODE_SKILLS_DIR, name)
    try:
        if os.path.islink(symlink_path):
            os.unlink(symlink_path)
        os.symlink(skill_dir, symlink_path)
    except Exception as e:
        return {"status": "error", "message": f"The error of the symlink creation: {e}"}
        
    # The update of the CONTEXT.md
    ctx_file = os.path.join(SKILLS_DIR, "CONTEXT.md")
    if os.path.exists(ctx_file):
        with open(ctx_file, "a", encoding="utf-8") as f:
            f.write(f"\n- [[{name}/SKILL|{name}]] — {desc}")

    # 1. The auto-registration in the skills/README.md
    readme_file = os.path.join(SKILLS_DIR, "README.md")
    if os.path.exists(readme_file):
        with open(readme_file, "r", encoding="utf-8") as rf:
            rc = rf.read()
        if f"| {name} |" not in rc:
            entry = f"| {name} | {desc} | and_os/lib/skills/{name}/SKILL.md |\n"
            if "| health-orchestrator |" in rc:
                rc = rc.replace("| health-orchestrator |", entry + "| health-orchestrator |")
            else:
                rc = rc + entry
            with open(readme_file, "w", encoding="utf-8") as rf:
                rf.write(rc)

    # 2. The auto-registration in the skills/ROUTING.md (Section 3 Meta/Domain)
    routing_file = os.path.join(SKILLS_DIR, "ROUTING.md")
    if os.path.exists(routing_file):
        with open(routing_file, "r", encoding="utf-8") as rtf:
            rtc = rtf.read()
        if f"`{name}`" not in rtc:
            table_row = f"| `{name}` | {desc[:40]} | ⚡ {domain} | and_os/lib/skills/{name}/ | {name}, {domain.lower()} |\n"
            if "## 🧭 3." in rtc:
                rtc = rtc + table_row
            with open(routing_file, "w", encoding="utf-8") as rtf:
                rtf.write(rtc)

    # 3. The synchronization of the global manifests (Rule #54 & #55)
    actual_skills_count = len([
        d for d in os.listdir(SKILLS_DIR)
        if os.path.isdir(os.path.join(SKILLS_DIR, d)) and os.path.exists(os.path.join(SKILLS_DIR, d, "SKILL.md"))
    ])

    manifest_updates = [
        (os.path.join(VAULT_ROOT, "AGENTS.md"), r"реестр \d+ скиллов", f"реестр {actual_skills_count} скиллов"),
        (os.path.join(VAULT_ROOT, "and_os/etc/SYSTEM_MAP.md"), r"\d+ [Aa]ctive [Ss]kills", f"{actual_skills_count} Active Skills"),
        (os.path.join(VAULT_ROOT, "and_os/etc/SYSTEM_MAP.md"), r"Registry of \d+ Skills", f"Registry of {actual_skills_count} Skills"),
        (os.path.join(VAULT_ROOT, "and_os/etc/SYSTEM_ARCHITECTURE_GRAPH.md"), r"\d+ Active Skills", f"{actual_skills_count} Active Skills"),
        (os.path.join(VAULT_ROOT, "and_os/lib/skills/README.md"), r"\d+ active skills", f"{actual_skills_count} active skills")
    ]
    import re
    for m_path, pat, repl in manifest_updates:
        if os.path.exists(m_path):
            with open(m_path, "r", encoding="utf-8") as mf:
                mc = mf.read()
            new_mc = re.sub(pat, repl, mc)
            if new_mc != mc:
                with open(m_path, "w", encoding="utf-8") as mf:
                    mf.write(new_mc)

    # 4. The update of the SKILL_BINDINGS.json
    bindings_file = os.path.join(VAULT_ROOT, "and_os", "etc", "SKILL_BINDINGS.json")
    if os.path.exists(bindings_file):
        try:
            with open(bindings_file, "r", encoding="utf-8") as bf:
                b_data = json.load(bf)
            b_data[name] = {
                "name": name,
                "modality": "DECLARATIVE_KNOWLEDGE",
                "engine": None,
                "path": f"and_os/lib/skills/{name}",
                "has_references": False
            }
            with open(bindings_file, "w", encoding="utf-8") as bf:
                json.dump(b_data, bf, indent=2, ensure_ascii=False)
        except (OSError, TypeError) as e:
            sys.stderr.write(f"[register_component] Warning writing bindings: {e}\n")

    # 5. The cascading propagation of the dependencies (Rule #54)
    dep_script = os.path.join(VAULT_ROOT, "and_os", "bin", "dependency_engine.py")
    if os.path.exists(dep_script):
        subprocess.run([sys.executable, dep_script, "--propagate"], capture_output=True, text=True)

    # 6. The launch of the Health Grid audit (Triple Green Protocol)
    val_script = os.path.join(VAULT_ROOT, "and_os", "bin", "validate_system.py")
    val_res = subprocess.run([sys.executable, val_script, "--check"], capture_output=True, text=True)
    
    return {
        "status": "ok",
        "action": "SKILL_REGISTERED",
        "skill_name": name,
        "path": skill_dir,
        "symlink": symlink_path,
        "domain": domain,
        "total_skills": actual_skills_count,
        "validation_passed": val_res.returncode == 0
    }

def register_module(hub: str, name: str, source_file: str, role: str, commands: list) -> dict:
    """Registers the new python module into the target facade hub (doc_hub, tracker_hub, cg_workspace, terminal)."""
    try:
        from and_os.lib.core.root_config import resolve_pulsar_root
        pulsar_root = resolve_pulsar_root() or os.path.expanduser("./pulsar")
    except Exception:
        pulsar_root = os.path.expanduser("./pulsar")
    if hub in ["terminal", "and_terminal"]:
        hub_dir = os.path.join(pulsar_root, "AND_Terminal")
    else:
        hub_dir = os.path.join(APPS_DIR, hub)
        
    if not os.path.exists(hub_dir):
        return {"status": "error", "message": f"The hub {hub} was not found in the {APPS_DIR} or the {pulsar_root}"}
        
    modules_dir = os.path.join(hub_dir, "modules")
    os.makedirs(modules_dir, exist_ok=True)
    
    filename = f"{name}.py" if not name.endswith(".py") else name
    target_mod_path = os.path.join(modules_dir, filename)
    
    if not os.path.exists(source_file):
        return {"status": "error", "message": f"The source file {source_file} was not found"}
        
    try:
        py_compile.compile(source_file, doraise=True)
    except py_compile.PyCompileError as e:
        return {"status": "error", "message": f"The syntax error in the {source_file}: {e}"}
        
    with open(source_file, "r", encoding="utf-8") as sf:
        code = sf.read()
    with open(target_mod_path, "w", encoding="utf-8") as tf:
        tf.write(code)
        
    reg_file = os.path.join(hub_dir, "modules_registry.json")
    if not os.path.exists(reg_file):
        reg_file = os.path.join(hub_dir, "pipeline_modules.json")
        
    registry_updated = False
    if os.path.exists(reg_file):
        with open(reg_file, "r", encoding="utf-8") as rf:
            reg_data = json.load(rf)
            
        mods = reg_data.setdefault("modules", {})
        mod_key = name.replace(".py", "")
        mods[mod_key] = {
            "file": filename,
            "version": "1.0.0",
            "role": role,
            "commands": commands,
            "last_modified": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        reg_data["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        with open(reg_file, "w", encoding="utf-8") as rf:
            json.dump(reg_data, rf, indent=2, ensure_ascii=False)
        registry_updated = True
    else:
        # Create initial registry
        reg_data = {
            "hub": hub,
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "modules": {
                name.replace(".py", ""): {
                    "file": filename,
                    "version": "1.0.0",
                    "role": role,
                    "commands": commands,
                    "last_modified": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                }
            }
        }
        with open(reg_file, "w", encoding="utf-8") as rf:
            json.dump(reg_data, rf, indent=2, ensure_ascii=False)
        registry_updated = True
        
    return {
        "status": "ok",
        "action": "MODULE_REGISTERED",
        "hub": hub,
        "module_name": name.replace(".py", ""),
        "target_file": target_mod_path,
        "role": role,
        "commands": commands,
        "registry_updated": registry_updated
    }

def main():
    parser = argparse.ArgumentParser(description="AnD os v1.0.0 Component Registrar")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # 1. new-skill
    p_sk = subparsers.add_parser("new-skill", help="Create and register the new skill")
    p_sk.add_argument("--name", required=True, help="The name of the skill (kebab-case, e.g. my-tool)")
    p_sk.add_argument("--desc", required=True, help="The brief description of the purpose")
    p_sk.add_argument("--domain", default="General", help="The domain of the skill")
    p_sk.add_argument("--tags", help="The tags separated by a comma")
    
    # 2. new-module
    p_mod = subparsers.add_parser("new-module", help="Register the new script into the module hub")
    p_mod.add_argument("--hub", choices=["doc_hub", "tracker_hub", "cg_workspace", "terminal"], required=True, help="The target hub")
    p_mod.add_argument("--name", required=True, help="The name of the module (snake_case)")
    p_mod.add_argument("--src", required=True, help="The path to the source .py file")
    p_mod.add_argument("--role", required=True, help="The description of the role of the module")
    p_mod.add_argument("--commands", default="", help="The commands separated by a comma")
    
    args = parser.parse_args()
    
    if args.command == "new-skill":
        tags = [t.strip() for t in args.tags.split(",")] if args.tags else None
        res = register_skill(args.name, args.desc, args.domain, tags)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        
    elif args.command == "new-module":
        cmds = [c.strip() for c in args.commands.split(",")] if args.commands else [args.name]
        res = register_module(args.hub, args.name, args.src, args.role, cmds)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
