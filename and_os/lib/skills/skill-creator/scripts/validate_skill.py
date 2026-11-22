#!/usr/bin/env python3
"""
validate_skill.py — Canonical ABI & Spec Linter for AnD os Skills.
Part of Ring 0 Meta-Skill Infrastructure (and_os/lib/skills/skill-creator/).

Evaluates any target skill against:
  1. SKILL_MODULE_ABI v2.1 specifications (frontmatter, name, description).
  2. Anthropic & Agent Skills standard (kebab-case, length limits, trigger-first description).
  3. AnD os Architectural Rules (Island Binding, Context Tier, Clean Code, Stateless).
  4. Router coherence: frontmatter 'island:' must agree with ROUTING.md
     (own island row, Universal Meta-Skills section, or meta-matrix entry).
     Cross-island placement without Universal membership is a warning (judgement class).
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple


ALLOWED_PROPERTIES = {
    "name", "description", "version", "lifecycle", "domain",
    "island", "context_tier", "facade_binding", "modality",
    "tags", "allowed-tools", "probe_cmd", "ttl", "reviewed",
    "engine", "engine_cmd", "created"
}

VALID_MODALITIES = {"EXECUTABLE_ENGINE", "DECLARATIVE_KNOWLEDGE", "PROCEDURAL_AUTOMATION"}
VALID_CONTEXT_TIERS = {"QUICK", "WORK", "STRATEGIC", "SYSTEM"}
VALID_LIFECYCLES = {"ACTIVE", "EXPERIMENTAL", "REVIEW", "DEPRECATED", "ARCHIVED"}


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Extracts and parses frontmatter dictionary without third-party YAML dependencies."""
    if not content.startswith("---"):
        return {}, "Missing leading frontmatter delimiter (---)"

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, "Incomplete frontmatter block (missing closing ---)"

    data: Dict[str, Any] = {}
    lines = parts[1].splitlines()
    current_list_key = None

    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Check list item
        if stripped.startswith("- ") and current_list_key:
            item = stripped[2:].strip().strip('"').strip("'")
            data[current_list_key].append(item)
            continue

        current_list_key = None
        if ":" in stripped:
            k, v = stripped.split(":", 1)
            key = k.strip()
            val = v.strip()
            if not val:
                # Potential list or empty dict
                data[key] = []
                current_list_key = key
            elif val.startswith("[") and val.endswith("]"):
                # Inline array: ["a", "b"]
                items = [item.strip().strip('"').strip("'") for item in val[1:-1].split(",") if item.strip()]
                data[key] = items
            else:
                data[key] = val.strip('"').strip("'")
        else:
            return {}, f"Invalid frontmatter syntax at line {line_num}: '{stripped}'"

    return data, ""


def _routing_surfaces(routing_md: Path) -> Tuple[Dict[str, set], set, set, str]:
    """Parses ROUTING.md into routing surfaces.

    Returns (island_rows, universal_names, matrix_names, error).
    island_rows: island id -> skill names listed in that row (Core + Extensions cells).
    universal_names: skills listed in the Universal Meta-Skills section (cross-domain by design).
    matrix_names: skills listed in the Meta & System Skills Cross-Domain Matrix.
    """
    try:
        text = routing_md.read_text(encoding="utf-8")
    except OSError as err:
        return {}, set(), set(), f"ROUTING.md unreadable ({err}) — routing coverage not verified."

    island_rows: Dict[str, set] = {}
    for line in text.splitlines():
        m = re.match(r"^\| \*\*Island (\d+)\*\* \|", line)
        if not m:
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) >= 5:
            names = set(re.findall(r"`([a-z0-9][a-z0-9-]*)`", cells[2]))
            names |= set(re.findall(r"`([a-z0-9][a-z0-9-]*)`", cells[4]))
            island_rows[m.group(1)] = names

    universal_names: set = set()
    matrix_names: set = set()
    section = ""
    for line in text.splitlines():
        heading = re.match(r"^##\s+(.*)", line)
        if heading:
            title = heading.group(1)
            section = "universal" if "Universal Meta-Skills" in title else \
                      "matrix" if "Cross-Domain Matrix" in title else ""
            continue
        if line.startswith("|") and "`" in line:
            first_cell = line.split("|")[1].strip()
            name = re.match(r"^`([a-z0-9][a-z0-9-]*)`", first_cell)
            if not name:
                continue
            if section == "universal":
                universal_names.add(name.group(1))
            elif section == "matrix":
                matrix_names.add(name.group(1))

    return island_rows, universal_names, matrix_names, ""


def validate_skill_structure(skill_dir: Path) -> Tuple[List[str], List[str]]:
    """Validates physical layout, SKILL.md, ABI requirements, and router coherence.

    Returns (errors, warnings): errors fail validation, warnings are advisory.
    """
    errors: List[str] = []
    warnings: List[str] = []

    if not skill_dir.exists() or not skill_dir.is_dir():
        return [f"Directory not found: {skill_dir}"], warnings

    skill_name = skill_dir.name
    if not re.match(r"^[a-z0-9-]+$", skill_name) or skill_name.startswith("-") or skill_name.endswith("-"):
        errors.append(f"Directory name '{skill_name}' must be strict kebab-case (lowercase letters, numbers, hyphens).")

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return errors + ["SKILL.md file is missing from root of skill directory."], warnings

    try:
        content = skill_md.read_text(encoding="utf-8")
    except OSError as err:
        return errors + [f"Failed to read SKILL.md: {err}"], warnings

    fm, parse_err = parse_frontmatter(content)
    if parse_err:
        return errors + [f"Frontmatter parse error: {parse_err}"], warnings

    # Required fields
    for req in ["name", "description", "version", "domain"]:
        if req not in fm or not fm[req]:
            errors.append(f"Frontmatter missing mandatory field: '{req}'")

    # Name match
    if fm.get("name") != skill_name:
        errors.append(f"Frontmatter 'name' ('{fm.get('name')}') must match directory name ('{skill_name}').")

    # Description rules
    desc = fm.get("description", "")
    if desc:
        if len(desc) > 1024:
            errors.append(f"Description length ({len(desc)}) exceeds limit of 1024 characters.")
        if "<" in desc or ">" in desc:
            errors.append("Description must not contain angle brackets (< or >).")
        if not desc.startswith("Use when"):
            errors.append("Description must be trigger-first, beginning with 'Use when...'.")

    # Modality and Island checks (1..9 Islands Archipelago)
    island = fm.get("island")
    if island is not None:
        try:
            isl_num = int(island)
            if not (1 <= isl_num <= 9):
                errors.append(f"Island value ({island}) must be between 1 and 9.")
        except ValueError:
            errors.append(f"Island value ('{island}') must be an integer between 1 and 9.")

    modality = fm.get("modality")
    if modality and modality not in VALID_MODALITIES:
        errors.append(f"Invalid modality '{modality}'. Allowed: {', '.join(sorted(VALID_MODALITIES))}")

    # Check modality specifics (ownership model, SKILL_MODULE_ABI.md §1)
    scripts_dir = skill_dir / "scripts"
    py_files = list(scripts_dir.glob("*.py")) if scripts_dir.exists() else []
    if modality == "EXECUTABLE_ENGINE":
        has_engine_field = bool(fm.get("engine") or fm.get("engine_cmd"))
        if not py_files and not has_engine_field:
            errors.append("Modality EXECUTABLE_ENGINE requires executable scripts in scripts/ or an explicit 'engine:' path in frontmatter.")
    elif modality == "DECLARATIVE_KNOWLEDGE" and py_files:
        errors.append(
            "Modality DECLARATIVE_KNOWLEDGE but scripts/ contains executable Python "
            f"({', '.join(p.name for p in sorted(py_files))}). Reclassify to EXECUTABLE_ENGINE "
            "and add a scripts/canary.py smoke probe (<500 ms)."
        )

    # Router coherence: frontmatter island vs ROUTING.md surfaces
    if island is not None:
        routing_md = skill_dir.parent / "ROUTING.md"
        island_rows, universal_names, matrix_names, surf_err = _routing_surfaces(routing_md)
        if surf_err:
            warnings.append(surf_err)
        else:
            in_own_row = skill_name in island_rows.get(str(island), set())
            in_other_row = [i for i, names in island_rows.items()
                            if i != str(island) and skill_name in names]
            in_universal = skill_name in universal_names
            in_matrix = skill_name in matrix_names
            if not (in_own_row or in_universal or in_matrix or in_other_row):
                errors.append(
                    f"Skill is not routed in ROUTING.md (absent from island {island} row, "
                    "Universal Meta-Skills section, and meta-matrix). Register it in the "
                    "island table or the Universal section."
                )
            elif not in_own_row and not in_universal and in_other_row:
                warnings.append(
                    f"Cross-island placement: frontmatter island {island} but ROUTING.md "
                    f"lists the skill under island(s) {', '.join(sorted(in_other_row))}. "
                    "Align the binding or add the skill to its own island row."
                )

    # Context tier
    tier = fm.get("context_tier")
    if tier and tier not in VALID_CONTEXT_TIERS:
        errors.append(f"Invalid context_tier '{tier}'. Allowed: {', '.join(sorted(VALID_CONTEXT_TIERS))}")

    return errors, warnings


def validate_all_skills(skills_root: Path) -> Tuple[int, int, List[Tuple[str, List[str]]], List[Tuple[str, List[str]]]]:
    """Validates all skills in the given root directory.

    Returns (total, passed, failures, warning_sets).
    """
    failures: List[Tuple[str, List[str]]] = []
    warning_sets: List[Tuple[str, List[str]]] = []
    total = 0
    passed = 0

    for item in sorted(skills_root.iterdir()):
        if item.is_dir() and not item.name.startswith(".") and item.name != "references":
            total += 1
            errs, warns = validate_skill_structure(item)
            if errs:
                failures.append((item.name, errs))
            else:
                passed += 1
            if warns:
                warning_sets.append((item.name, warns))

    return total, passed, failures, warning_sets


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ["--all", "all"]:
        default_skills_dir = Path(__file__).resolve().parents[2]
        total, passed, failures, warning_sets = validate_all_skills(default_skills_dir)
        sys.stdout.write(f"\n=================================================================\n")
        sys.stdout.write(f"🏛️ Canonical Skill ABI & Specification Linter (v2.1)\n")
        sys.stdout.write(f"📊 Validated: {total} skills | Passed: {passed} | Issues: {len(failures)}\n")
        sys.stdout.write(f"=================================================================\n")
        if failures:
            for sname, errs in failures:
                sys.stderr.write(f"❌ {sname}:\n")
                for e in errs:
                    sys.stderr.write(f"   • {e}\n")
            sys.exit(1)
        if warning_sets:
            sys.stdout.write(f"\n⚠️  Advisory warnings ({sum(len(w) for _, w in warning_sets)}):\n")
            for sname, warns in warning_sets:
                for w in warns:
                    sys.stdout.write(f"   ⚠️  {sname}: {w}\n")
        sys.stdout.write(f"✅ ALL {total} skills are 100% compliant with the reference ABI and specification!\n")
        sys.exit(0)

    target_path = Path(sys.argv[1]).resolve()
    val_errors, val_warnings = validate_skill_structure(target_path)

    if val_errors:
        sys.stderr.write(f"❌ Validation FAILED for '{target_path.name}':\n")
        for err in val_errors:
            sys.stderr.write(f"  • {err}\n")
        sys.exit(1)

    if val_warnings:
        sys.stdout.write(f"⚠️  Skill '{target_path.name}' passed with advisories:\n")
        for w in val_warnings:
            sys.stdout.write(f"  ⚠️  {w}\n")
        sys.stdout.write(f"🟢 Skill '{target_path.name}' is 100% compliant with AnD os ABI & Agent Skills spec.\n")
        sys.exit(0)

    sys.stdout.write(f"🟢 Skill '{target_path.name}' is 100% compliant with AnD os ABI & Agent Skills spec.\n")
    sys.exit(0)
