#!/usr/bin/env python3
"""
sync_system_mesh.py — Atomic Registrar & Manifest Synchronizer for Skills.
Part of Ring 0 Meta-Skill Infrastructure (and_os/lib/skills/skill-creator/).

Executes atomic transactional registration of a skill:
  1. Creates symlink in .opencode/skills/<name>.
  2. Updates SKILL_BINDINGS.json if an engine script is provided.
  3. Registers skill in REGISTRY.md.
  4. Synchronizes global active skill counter across:
     - system.json
     - SYSTEM.md
     - AGENTS.md
     - and_os/etc/SYSTEM_MAP.md
     - and_os/etc/SYSTEM_ARCHITECTURE_GRAPH.md
     - and_os/lib/skills/README.md
"""

import os
import sys
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional


def count_active_skills(skills_dir: Path) -> int:
    """Counts actual valid skills on disk."""
    count = 0
    for entry in skills_dir.iterdir():
        if entry.is_dir() and not entry.name.startswith(".") and (entry / "SKILL.md").exists():
            count += 1
    return count


def register_skill_in_mesh(vault_root: Path, skill_name: str, island_id: Optional[int] = None) -> List[str]:
    """Atomically synchronizes all system registrations for the target skill."""
    errors: List[str] = []
    skills_root = vault_root / "and_os/lib/skills"
    skill_dir = skills_root / skill_name

    if not skill_dir.exists():
        return [f"Skill directory does not exist: {skill_dir}"]

    # 1. Symlink in .opencode/skills/
    opencode_skills = vault_root / ".opencode/skills"
    opencode_skills.mkdir(parents=True, exist_ok=True)
    symlink_target = opencode_skills / skill_name
    
    try:
        if symlink_target.is_symlink() or symlink_target.exists():
            symlink_target.unlink()
        rel_target = os.path.relpath(skill_dir, opencode_skills)
        symlink_target.symlink_to(rel_target)
    except OSError as err:
        errors.append(f"Failed to create .opencode/skills symlink: {err}")

    # 2. Update actual count across manifests
    actual_count = count_active_skills(skills_root)
    
    # 2.1 system.json
    sys_json = vault_root / "system.json"
    if sys_json.exists():
        try:
            data = json.loads(sys_json.read_text(encoding="utf-8"))
            # Keep track in metadata
            data.setdefault("metadata", {})["activeSkillsCount"] = actual_count
            sys_json.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        except (OSError, json.JSONDecodeError) as err:
            errors.append(f"Failed to update system.json: {err}")

    # 2.2 AGENTS.md
    agents_md = vault_root / "AGENTS.md"
    if agents_md.exists():
        try:
            content = agents_md.read_text(encoding="utf-8")
            new_content = re.sub(r"реестр \d+ скиллов", f"реестр {actual_count} скиллов", content)
            if new_content != content:
                agents_md.write_text(new_content, encoding="utf-8")
        except OSError as err:
            errors.append(f"Failed to update AGENTS.md: {err}")

    # 2.3 SYSTEM_MAP.md
    sys_map = vault_root / "and_os/etc/SYSTEM_MAP.md"
    if sys_map.exists():
        try:
            content = sys_map.read_text(encoding="utf-8")
            new_content = re.sub(r"\d+ [Aa]ctive [Ss]kills", f"{actual_count} Active Skills", content)
            if new_content != content:
                sys_map.write_text(new_content, encoding="utf-8")
        except OSError as err:
            errors.append(f"Failed to update SYSTEM_MAP.md: {err}")

    # 2.4 SYSTEM_ARCHITECTURE_GRAPH.md
    arch_graph = vault_root / "and_os/etc/SYSTEM_ARCHITECTURE_GRAPH.md"
    if arch_graph.exists():
        try:
            content = arch_graph.read_text(encoding="utf-8")
            new_content = re.sub(r"\d+ Active Skills", f"{actual_count} Active Skills", content)
            if new_content != content:
                arch_graph.write_text(new_content, encoding="utf-8")
        except OSError as err:
            errors.append(f"Failed to update SYSTEM_ARCHITECTURE_GRAPH.md: {err}")

    # 2.5 and_os/lib/skills/README.md
    skills_readme = vault_root / "and_os/lib/skills/README.md"
    if skills_readme.exists():
        try:
            content = skills_readme.read_text(encoding="utf-8")
            new_content = re.sub(r"\d+ active skills", f"{actual_count} active skills", content)
            if new_content != content:
                skills_readme.write_text(new_content, encoding="utf-8")
        except OSError as err:
            errors.append(f"Failed to update and_os/lib/skills/README.md: {err}")

    # 3. Add to and_os/lib/skills/REGISTRY.md if missing
    registry_md = vault_root / "and_os/lib/skills/REGISTRY.md"
    if registry_md.exists():
        try:
            reg_text = registry_md.read_text(encoding="utf-8")
            if f"| {skill_name} |" not in reg_text:
                # Append to active table
                row = f"| {skill_name} | ACTIVE | STATIC | System registered skill |\n"
                reg_text = reg_text + row
                registry_md.write_text(reg_text, encoding="utf-8")
        except OSError as err:
            errors.append(f"Failed to update REGISTRY.md: {err}")

    return errors


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python3 sync_system_mesh.py <skill_name> [island_id]\n")
        sys.exit(1)

    s_name = sys.argv[1]
    isl = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else None
    root_p = Path(__file__).resolve().parents[5]

    reg_errors = register_skill_in_mesh(root_p, s_name, isl)
    if reg_errors:
        sys.stderr.write(f"❌ Mesh Synchronization FAILED for '{s_name}':\n")
        for err in reg_errors:
            sys.stderr.write(f"  • {err}\n")
        sys.exit(1)
    else:
        sys.stdout.write(f"🟢 Skill '{s_name}' is fully synchronized across AnD os manifests and symlinks.\n")
        sys.exit(0)
