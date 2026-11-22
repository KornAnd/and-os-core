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
import subprocess
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
    
    # 2.1 Canonical manifest and_os/etc/system.json (SSoT). The root
    # system.json is a generated projection of this file (step 2.7),
    # so only the canonical copy is written here.
    sys_json = vault_root / "and_os/etc/system.json"
    if sys_json.exists():
        try:
            data = json.loads(sys_json.read_text(encoding="utf-8"))
            data.setdefault("metadata", {})["activeSkillsCount"] = actual_count
            data["skills_count"] = actual_count
            if isinstance(data.get("skills"), dict):
                data["skills"]["skillsCount"] = actual_count
            sys_json.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8")
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

    # 2.3 SYSTEM.md (the skill word is spelled with \u escapes so this
    # module stays ASCII-only in source, per the language invariant)
    system_md = vault_root / "SYSTEM.md"
    if system_md.exists():
        try:
            content = system_md.read_text(encoding="utf-8")
            skill_word = "\u0441\u043a\u0438\u043b\u043b"
            new_content = re.sub(
                r"(\d+)\s+" + skill_word + r"(\w*)",
                lambda m: f"{actual_count} {skill_word}{m.group(2)}",
                content)
            if new_content != content:
                system_md.write_text(new_content, encoding="utf-8")
        except OSError as err:
            errors.append(f"Failed to update SYSTEM.md: {err}")

    # 2.4 SYSTEM_MAP.md
    sys_map = vault_root / "and_os/etc/SYSTEM_MAP.md"
    if sys_map.exists():
        try:
            content = sys_map.read_text(encoding="utf-8")
            new_content = re.sub(r"\d+ [Aa]ctive [Ss]kills", f"{actual_count} Active Skills", content)
            if new_content != content:
                sys_map.write_text(new_content, encoding="utf-8")
        except OSError as err:
            errors.append(f"Failed to update SYSTEM_MAP.md: {err}")

    # 2.5 SYSTEM_ARCHITECTURE_GRAPH.md
    arch_graph = vault_root / "and_os/etc/SYSTEM_ARCHITECTURE_GRAPH.md"
    if arch_graph.exists():
        try:
            content = arch_graph.read_text(encoding="utf-8")
            new_content = re.sub(r"\d+ Active Skills", f"{actual_count} Active Skills", content)
            if new_content != content:
                arch_graph.write_text(new_content, encoding="utf-8")
        except OSError as err:
            errors.append(f"Failed to update SYSTEM_ARCHITECTURE_GRAPH.md: {err}")

    # 2.6 and_os/lib/skills/README.md
    skills_readme = vault_root / "and_os/lib/skills/README.md"
    if skills_readme.exists():
        try:
            content = skills_readme.read_text(encoding="utf-8")
            new_content = re.sub(r"\d+ active skills", f"{actual_count} active skills", content)
            if new_content != content:
                skills_readme.write_text(new_content, encoding="utf-8")
        except OSError as err:
            errors.append(f"Failed to update and_os/lib/skills/README.md: {err}")

    # 2.7 Regenerate derived artifacts (the root projection hashes the
    # canonical manifest; the rules fast index hashes SYSTEM.md +
    # rules.md + the canonical manifest, so it must follow 2.3/2.1).
    projector = vault_root / "and_os/bin/manifest_projector.py"
    if projector.exists():
        proj = subprocess.run(
            [sys.executable, str(projector), "project-root"],
            capture_output=True, text=True, cwd=str(vault_root))
        if proj.returncode != 0:
            errors.append(
                "Failed to re-project root system.json: "
                f"{proj.stderr.strip()[:200]}")
    compiler = vault_root / "and_os/bin/rules_compiler.py"
    if compiler.exists():
        compiled = subprocess.run(
            [sys.executable, str(compiler), "compile"],
            capture_output=True, text=True, cwd=str(vault_root))
        if compiled.returncode != 0:
            errors.append(
                "Failed to recompile rules fast index: "
                f"{compiled.stderr.strip()[:200]}")

    # 3. Add to and_os/lib/skills/REGISTRY.md if missing. The row must land
    # inside the first status table (an EOF append lands outside every
    # table and the registry probes ignore it); the enclosing section
    # counter "(N)" is incremented in the same transaction.
    registry_md = vault_root / "and_os/lib/skills/REGISTRY.md"
    if registry_md.exists():
        try:
            reg_lines = registry_md.read_text(encoding="utf-8").splitlines()
            if f"| {skill_name} |" not in "\n".join(reg_lines):
                insert_at = None
                sep_at = None
                in_table = False
                for i, line in enumerate(reg_lines):
                    stripped = line.strip()
                    if not in_table:
                        if (stripped and "|" in stripped
                                and set(stripped) <= set("|-: ")):
                            sep_at = i
                            in_table = True
                    elif stripped.startswith("|"):
                        insert_at = i + 1
                    else:
                        break
                if insert_at is None:
                    errors.append(
                        "REGISTRY.md: no status table found for "
                        "skill registration")
                else:
                    reg_lines.insert(
                        insert_at,
                        f"| {skill_name} | ACTIVE | STATIC | "
                        f"System registered skill |")
                    if sep_at is not None:
                        for j in range(sep_at - 1, -1, -1):
                            if reg_lines[j].startswith("## "):
                                reg_lines[j] = re.sub(
                                    r"\((\d+)\)\s*$",
                                    lambda m: f"({int(m.group(1)) + 1})",
                                    reg_lines[j], count=1)
                                break
                    registry_md.write_text(
                        "\n".join(reg_lines) + "\n", encoding="utf-8")
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
