#!/usr/bin/env python3
"""
compile_skill.py — End-to-End Skill Synthesizer & Compiler for AnD os.
Part of Ring 0 Meta-Skill Infrastructure (and_os/lib/skills/skill-creator/).

Orchestrates complete atomic skill creation:
  1. Validates inputs (name, modality, island).
  2. Generates directory structure and SKILL.md.
  3. Validates structure and code hygiene via AST.
  4. Synchronizes manifests and symlinks via sync_system_mesh.py.
"""

import os
import sys
import argparse
from pathlib import Path

# Local helpers
CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))
from validate_skill import validate_skill_structure
from check_code_hygiene import inspect_skill_code
from sync_system_mesh import register_skill_in_mesh


ENGINE_TEMPLATE = """---
name: {name}
description: "{description}"
version: "1.0.0"
lifecycle: ACTIVE
domain: {domain}
island: {island}
context_tier: {tier}
facade_binding: "{facade}"
modality: EXECUTABLE_ENGINE
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob"]
probe_cmd: "python3 and_os/lib/skills/{name}/scripts/canary.py"
---

# {title}

## 1. Intent & Architectural Boundary
- **Purpose**: {description}
- **Island**: Island {island}
- **Modality**: EXECUTABLE_ENGINE

## 2. Trigger Matrix
- **When to activate**: Triggered on {trigger_words}.
- **When NOT to activate**: Do not activate for out-of-domain tasks.

## 3. Execution Protocol
1. Input verification.
2. Execute primary script via facade: `python3 and_os/lib/skills/{name}/scripts/{name}_engine.py --json`.
3. Validate stdout and return response.

## 4. Canary Verification
- Run: `python3 and_os/lib/skills/{name}/scripts/canary.py`
"""

KNOWLEDGE_TEMPLATE = """---
name: {name}
description: "{description}"
version: "1.0.0"
lifecycle: ACTIVE
domain: {domain}
island: {island}
context_tier: {tier}
facade_binding: "{facade}"
modality: DECLARATIVE_KNOWLEDGE
allowed-tools: ["Read", "Grep", "Glob"]
---

# {title}

## 1. Intent & Methodological Boundary
- **Purpose**: {description}
- **Island**: Island {island}
- **Modality**: DECLARATIVE_KNOWLEDGE

## 2. Trigger Matrix
- **When to activate**: Triggered on {trigger_words}.
- **When NOT to activate**: Do not activate for computational execution tasks.

## 3. Decision Framework & Guidance
- Read topic references under `and_os/lib/skills/{name}/references/`.
- Adhere to Dual-Language Policy (Rule #3).
"""

CANARY_SCRIPT_TEMPLATE = """#!/usr/bin/env python3
import sys

def canary_test():
    # Smoke check for skill
    return 0

if __name__ == "__main__":
    sys.exit(canary_test())
"""

ENGINE_SCRIPT_TEMPLATE = """#!/usr/bin/env python3
import sys
import json
import argparse

def main():
    parser = argparse.ArgumentParser(description="{name} engine")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()

    payload = {{"status": "ok", "skill": "{name}"}}
    if args.json:
        print(json.dumps(payload))
    else:
        print(f"Skill '{name}' executed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""


def compile_new_skill(
    name: str,
    description: str,
    domain: str,
    island: int,
    modality: str,
    tier: str = "WORK",
    facade: str = "sys_cli"
) -> bool:
    vault_root = CURRENT_DIR.parents[4]
    skills_root = vault_root / "and_os/lib/skills"
    target_skill_dir = skills_root / name

    if target_skill_dir.exists():
        sys.stderr.write(f"❌ Error: Skill directory already exists: {target_skill_dir}\n")
        return False

    title = " ".join(word.capitalize() for word in name.split("-"))
    trigger_words = ", ".join(name.split("-"))

    # Create directories
    target_skill_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir = target_skill_dir / "scripts"
    refs_dir = target_skill_dir / "references"

    scripts_dir.mkdir(exist_ok=True)
    refs_dir.mkdir(exist_ok=True)

    # Write SKILL.md
    if modality == "EXECUTABLE_ENGINE":
        skill_content = ENGINE_TEMPLATE.format(
            name=name, description=description, domain=domain,
            island=island, tier=tier, facade=facade, title=title,
            trigger_words=trigger_words
        )
        # Write starter scripts
        (scripts_dir / "canary.py").write_text(CANARY_SCRIPT_TEMPLATE, encoding="utf-8")
        engine_script = ENGINE_SCRIPT_TEMPLATE.format(name=name)
        (scripts_dir / f"{name}_engine.py").write_text(engine_script, encoding="utf-8")
    else:
        skill_content = KNOWLEDGE_TEMPLATE.format(
            name=name, description=description, domain=domain,
            island=island, tier=tier, facade=facade, title=title,
            trigger_words=trigger_words
        )
        (refs_dir / "GUIDELINES.md").write_text(f"# {title} Reference Guidelines\n\nMethodological documentation.", encoding="utf-8")

    (target_skill_dir / "SKILL.md").write_text(skill_content, encoding="utf-8")

    # Validate structure and code hygiene
    struct_errors = validate_skill_structure(target_skill_dir)
    if struct_errors:
        sys.stderr.write(f"❌ Structural validation failed for '{name}':\n")
        for e in struct_errors:
            sys.stderr.write(f"  • {e}\n")
        return False

    hygiene_errors = inspect_skill_code(target_skill_dir)
    if hygiene_errors:
        sys.stderr.write(f"❌ Code hygiene failed for '{name}':\n")
        for e in hygiene_errors:
            sys.stderr.write(f"  • {e}\n")
        return False

    # Synchronize mesh
    sync_errors = register_skill_in_mesh(vault_root, name, island)
    if sync_errors:
        sys.stderr.write(f"❌ Mesh sync failed for '{name}':\n")
        for e in sync_errors:
            sys.stderr.write(f"  • {e}\n")
        return False

    print(f"🟢 Successfully compiled and registered '{name}' (Island {island}, {modality}) into AnD os mesh!")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compile and register a new skill into AnD os.")
    parser.add_argument("name", help="Kebab-case skill name")
    parser.add_argument("--description", required=True, help="Trigger-first description starting with 'Use when...'")
    parser.add_argument("--domain", default="system", help="Skill domain (system, production, etc.)")
    parser.add_argument("--island", type=int, default=8, help="Island ID (1..8)")
    parser.add_argument("--modality", choices=["EXECUTABLE_ENGINE", "DECLARATIVE_KNOWLEDGE"], default="DECLARATIVE_KNOWLEDGE")
    parser.add_argument("--tier", choices=["QUICK", "WORK", "STRATEGIC"], default="WORK")
    parser.add_argument("--facade", default="sys_cli", help="Target facade binding")

    args = parser.parse_args()
    success = compile_new_skill(
        name=args.name,
        description=args.description,
        domain=args.domain,
        island=args.island,
        modality=args.modality,
        tier=args.tier,
        facade=args.facade
    )
    sys.exit(0 if success else 1)
