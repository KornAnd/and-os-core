#!/usr/bin/env python3
"""
skill_bus.py — Microkernel Skill Bus & Interop Engine (AnD os v8.1)
Universal gateway for all 58 system skills:
  - inspect: zero-token architecture summary and bindings introspection
  - run: uniform execution of skill engine scripts with telemetry logging
  - ref: 0-token topical reference extraction (saving 95% prompt tokens)
  - pipe: standard Unix-like data chaining between modular skills
  - list: discover skills grouped by domain and modality

Complies with Rule #16 (Think in Code), Rule #44 (Context Bundling),
Rule #50 (Stateless FHS), Rule #51 (Microkernel Bus Decoupling), and Rule #54.
"""

import os
import sys
import json
import argparse
import subprocess
from typing import Dict, Any, List, Optional

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SKILLS_DIR = os.path.join(VAULT_ROOT, "and_os", "lib", "skills")
BINDINGS_PATH = os.path.join(VAULT_ROOT, "and_os", "etc", "SKILL_BINDINGS.json")

def load_bindings() -> Dict[str, Any]:
    """Load canonical skill bindings registry."""
    if os.path.exists(BINDINGS_PATH):
        try:
            with open(BINDINGS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            sys.stderr.write(f"[skill_bus] Warning reading bindings: {e}\n")
    return {}

def parse_frontmatter(content: str) -> Dict[str, Any]:
    """Lightweight pure-python frontmatter parser."""
    res = {}
    if not content.startswith("---"):
        return res
    parts = content.split("---", 2)
    if len(parts) < 3:
        return res
    for line in parts[1].splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            res[key.strip()] = val.strip().strip('"').strip("'")
    return res

def inspect_skill(skill_name: str) -> Dict[str, Any]:
    """Inspect skill metadata, modality, and capabilities."""
    bindings = load_bindings()
    binding = bindings.get(skill_name, {})
    
    skill_dir = os.path.join(SKILLS_DIR, skill_name)
    skill_md = os.path.join(skill_dir, "SKILL.md")
    
    if not os.path.exists(skill_md):
        return {"error": f"Skill '{skill_name}' not found on filesystem."}
    
    with open(skill_md, "r", encoding="utf-8") as f:
        content = f.read()
    
    fm = parse_frontmatter(content)
    engine = binding.get("engine")
    engine_exists = os.path.exists(os.path.join(VAULT_ROOT, engine)) if engine else False
    
    # Discover references
    refs = []
    refs_dir = os.path.join(skill_dir, "references")
    if os.path.exists(refs_dir):
        for root, _, files in os.walk(refs_dir):
            for file in files:
                if file.endswith(".md"):
                    rel_p = os.path.relpath(os.path.join(root, file), skill_dir)
                    refs.append(rel_p)

    return {
        "name": skill_name,
        "modality": binding.get("modality", "DECLARATIVE_KNOWLEDGE"),
        "version": fm.get("version", "1.0.0"),
        "lifecycle": fm.get("lifecycle", "ACTIVE"),
        "ttl": fm.get("ttl", "STATIC"),
        "engine": engine,
        "engine_available": engine_exists,
        "has_references": len(refs) > 0,
        "references": refs,
        "description": fm.get("description", "")
    }

def run_skill(skill_name: str, args: List[str], json_mode: bool = False) -> int:
    """Execute the skill's bound Python engine with supplied arguments."""
    bindings = load_bindings()
    binding = bindings.get(skill_name)
    if not binding or not binding.get("engine"):
        # Fallback to direct check
        candidate = os.path.join(VAULT_ROOT, "and_os", "bin", f"{skill_name.replace('-', '_')}.py")
        if os.path.exists(candidate):
            engine_path = candidate
        else:
            print(f"❌ Skill '{skill_name}' operates in DECLARATIVE_KNOWLEDGE mode and has no executable engine.", file=sys.stderr)
            print(f"💡 Read the protocol via: sys_cli.py skill info {skill_name}", file=sys.stderr)
            return 1
    else:
        engine_path = os.path.join(VAULT_ROOT, binding["engine"])

    if not os.path.exists(engine_path):
        print(f"❌ Bound engine script does not exist: {engine_path}", file=sys.stderr)
        return 1

    cmd = [sys.executable, engine_path] + args
    if json_mode and "--json" not in args:
        cmd.append("--json")

    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, file=sys.stderr, end="")
    return proc.returncode

def extract_references(skill_name: str, topic: Optional[str] = None, list_only: bool = False) -> Dict[str, Any]:
    """Extract sections from references without blowing up context window (Rule #44)."""
    skill_dir = os.path.join(SKILLS_DIR, skill_name)
    refs_dir = os.path.join(skill_dir, "references")
    
    target_md_files = []
    if os.path.exists(refs_dir):
        for root, _, files in os.walk(refs_dir):
            for f in sorted(files):
                if f.endswith(".md"):
                    target_md_files.append((os.path.join(root, f), os.path.relpath(os.path.join(root, f), refs_dir)))

    # Fallback to SKILL.md itself if references/ has no markdown files
    if not target_md_files:
        skill_md = os.path.join(skill_dir, "SKILL.md")
        if os.path.exists(skill_md):
            target_md_files.append((skill_md, "SKILL.md"))

    topics_found = {}
    for file_path, rel_file in target_md_files:
        with open(file_path, "r", encoding="utf-8") as rf:
            lines = rf.readlines()
        
        cur_header = "Intro"
        cur_content = []
        for line in lines:
            if line.startswith("#"):
                if cur_content:
                    topics_found[f"{rel_file}::{cur_header}"] = "".join(cur_content).strip()
                cur_header = line.strip().lstrip("#").strip()
                cur_content = [line]
            else:
                cur_content.append(line)
        if cur_content:
            topics_found[f"{rel_file}::{cur_header}"] = "".join(cur_content).strip()

    if list_only:
        return {"skill": skill_name, "topics": list(topics_found.keys())}

    if topic:
        topic_lower = topic.lower()
        matches = {k: v for k, v in topics_found.items() if topic_lower in k.lower()}
        if matches:
            return {"skill": skill_name, "matches": matches}
        return {"skill": skill_name, "error": f"Topic '{topic}' not found.", "available": list(topics_found.keys())}

    # If neither, return top topics summary
    return {"skill": skill_name, "topics": list(topics_found.keys())}

def pipe_skills(producer_name: str, consumer_name: str, initial_args: List[str]) -> int:
    """Chain output from producer skill into consumer skill."""
    bindings = load_bindings()
    if producer_name not in bindings or not bindings[producer_name].get("engine"):
        print(f"❌ Producer skill '{producer_name}' lacks executable engine.", file=sys.stderr)
        return 1
    if consumer_name not in bindings or not bindings[consumer_name].get("engine"):
        print(f"❌ Consumer skill '{consumer_name}' lacks executable engine.", file=sys.stderr)
        return 1

    prod_engine = os.path.join(VAULT_ROOT, bindings[producer_name]["engine"])
    cons_engine = os.path.join(VAULT_ROOT, bindings[consumer_name]["engine"])

    cmd_prod = [sys.executable, prod_engine] + initial_args
    if "--json" not in initial_args:
        cmd_prod.append("--json")

    # Run producer
    p_res = subprocess.run(cmd_prod, text=True, capture_output=True)
    if p_res.returncode != 0:
        print(f"❌ Producer '{producer_name}' failed with code {p_res.returncode}:\n{p_res.stderr}", file=sys.stderr)
        return p_res.returncode

    try:
        # Validate that producer gave valid JSON
        json_output = json.loads(p_res.stdout)
    except Exception as e:
        print(f"❌ Producer '{producer_name}' output is not valid JSON for piping: {e}", file=sys.stderr)
        return 1

    # Route based on consumer type
    cons_args = []
    if consumer_name == "editorial-otio-conform":
        # Check if output contains shots
        shots = json_output.get("shots") if isinstance(json_output, dict) else json_output
        seq_title = json_output.get("title", "Piped_Sequence")
        cons_args = [seq_title, "--shots", json.dumps(shots), "--handles", "8"]
    elif consumer_name == "hybrid-comfyui-render":
        # Extract first shot id if available
        shots = json_output.get("shots", [])
        shot_id = shots[0].get("shot_id", "sh_001") if shots else "sh_001"
        prompt = json_output.get("title", "Piped animation scene")
        cons_args = [shot_id, "--prompt", prompt]
    else:
        # Default pipe as --json-input
        cons_args = ["--input", json.dumps(json_output)]

    cmd_cons = [sys.executable, cons_engine] + cons_args
    c_res = subprocess.run(cmd_cons, text=True, capture_output=True)
    if c_res.stdout:
        print(c_res.stdout, end="")
    if c_res.stderr:
        print(c_res.stderr, file=sys.stderr, end="")
    return c_res.returncode

def main():
    parser = argparse.ArgumentParser(description="Microkernel Skill Bus (AnD os v8.1)")
    subparsers = parser.add_subparsers(dest="action", help="Action to perform")

    # list
    subparsers.add_parser("list", help="List all skills and their execution bindings")

    # info / inspect
    p_info = subparsers.add_parser("info", help="Inspect skill metadata and modality")
    p_info.add_argument("skill", help="Name of skill")
    p_info.add_argument("--json", action="store_true", help="Output JSON")

    # run
    p_run = subparsers.add_parser("run", help="Execute the skill engine")
    p_run.add_argument("skill", help="Name of skill")
    p_run.add_argument("args", nargs=argparse.REMAINDER, help="Arguments passed to skill engine")

    # ref
    p_ref = subparsers.add_parser("ref", help="0-Token topical reference extractor")
    p_ref.add_argument("skill", help="Name of skill")
    p_ref.add_argument("--topic", help="Topic or section to extract")
    p_ref.add_argument("--list", action="store_true", help="List available topics only")

    # pipe
    p_pipe = subparsers.add_parser("pipe", help="Pipe output from producer skill into consumer skill")
    p_pipe.add_argument("producer", help="Producer skill name")
    p_pipe.add_argument("consumer", help="Consumer skill name")
    p_pipe.add_argument("args", nargs=argparse.REMAINDER, help="Arguments for producer skill")

    args = parser.parse_args()

    if args.action == "list":
        bindings = load_bindings()
        print(f"📦 Total Registered Skills in Bus: {len(bindings)}")
        print(f"{'Skill Name':<28} | {'Modality':<22} | {'Engine'}")
        print("-" * 75)
        for name, b in sorted(bindings.items()):
            mod = b.get("modality", "DECLARATIVE")
            eng = b.get("engine") or "(declarative protocol)"
            print(f"{name:<28} | {mod:<22} | {eng}")
    elif args.action == "info":
        res = inspect_skill(args.skill)
        if args.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        elif "error" in res:
            print(f"❌ {res['error']}", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"🧩 Skill: {res.get('name')} (v{res.get('version')})")
            print(f"• Modality: {res.get('modality')}")
            print(f"• Lifecycle: {res.get('lifecycle')} | TTL: {res.get('ttl')}")
            print(f"• Engine: {res.get('engine') or 'None (Declarative knowledge)'}")
            print(f"• References: {len(res.get('references', []))} documents")
            print(f"• Description: {res.get('description')}")
    elif args.action == "run":
        raw_args = args.args
        if raw_args and raw_args[0] == "--":
            raw_args = raw_args[1:]
        sys.exit(run_skill(args.skill, raw_args))
    elif args.action == "ref":
        res = extract_references(args.skill, topic=args.topic, list_only=args.list)
        if args.list:
            print(f"📚 Available Reference Topics for '{args.skill}':")
            for t in res.get("topics", []):
                print(f"  - {t}")
        elif args.topic:
            matches = res.get("matches", {})
            if matches:
                for t_name, content in matches.items():
                    print(f"--- Topic: {t_name} ---")
                    print(content)
                    print()
            else:
                print(res.get("error", "No matching topics found."))
        else:
            print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.action == "pipe":
        raw_args = args.args
        if raw_args and raw_args[0] == "--":
            raw_args = raw_args[1:]
        sys.exit(pipe_skills(args.producer, args.consumer, raw_args))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
