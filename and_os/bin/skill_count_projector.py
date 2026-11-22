#!/usr/bin/env python3
"""
skill_count_projector.py — Single-source-of-truth projector for the
active-skills count (R-4, 20.11: closes the "skill-count drift" class —
51 places had to be re-synced by hand during the houdini-bridge SSoT
round, 19-20.11).

The count is measured on disk (and_os/lib/skills/<dir>/SKILL.md) and
projected, idempotently, onto every manifest/doc carrier. Running it
when the count is unchanged is a no-op (zero writes).

Carriers (measured 20.11):
  - and_os/etc/system.json                skills_count + metadata.activeSkillsCount
  - SYSTEM.md                             Skills Engine status line + monthly-audit line
  - and_os/lib/skills/CONTEXT.md          "Total Active Skills" line
  - and_os/lib/skills/ROUTING.md          "All N skills" mapping summary
  - and_os/lib/skills/README.md           "Currently registered" line
  - and_os/etc/SYSTEM_MAP.md              TL;DR + mermaid node
  - and_os/etc/SYSTEM_ARCHITECTURE_GRAPH.md  tldr + layer labels (x4)

Deliberately NOT projected (the drift gate, not the doc):
  - test pins asserting the exact count (they alert on drift by failing)
  - dependency_engine.propagate_updates keeps its own carrier list; both
    writers converge on the same on-disk value (no conflict).

Usage:
  skill_count_projector.py [--json] [--dry-run]
Exit: 0 = in sync (or just synced), 2 = usage error.
"""

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Tuple

sys.dont_write_bytecode = True

VAULT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def count_skills(vault_root: str) -> int:
    """Active skills = skill dirs on disk carrying a SKILL.md."""
    skills_path = os.path.join(vault_root, "and_os", "lib", "skills")
    if not os.path.isdir(skills_path):
        return 0
    return len([
        d for d in os.listdir(skills_path)
        if os.path.isdir(os.path.join(skills_path, d))
        and os.path.exists(os.path.join(skills_path, d, "SKILL.md"))
    ])


# (relative path, [(regex pattern, replacement template with {n})...])
# Patterns are deliberately narrow: they target the exact carrier
# sentences, never a bare number (other "N" in the same files are
# different facts and must not be touched).
CARRIERS: List[Tuple[str, List[Tuple[str, str]]]] = [
    ("and_os/etc/system.json", [
        (r'"activeSkillsCount": \d+', '"activeSkillsCount": {n}'),
        (r'"skills_count": \d+', '"skills_count": {n}'),
    ]),
    ("SYSTEM.md", [
        (r"\*\*\d+ active skills\*\* \(SOS: \d+/\d+ valid\)",
         "**{n} active skills** (SOS: {n}/{n} valid)"),
        (r"целостности \d+ скиллов", "целостности {n} скиллов"),
    ]),
    ("and_os/lib/skills/CONTEXT.md", [
        (r"\d+ active skills", "{n} active skills"),
    ]),
    ("and_os/lib/skills/ROUTING.md", [
        (r"All \d+ skills across", "All {n} skills across"),
    ]),
    ("and_os/lib/skills/README.md", [
        (r"\d+ active skills", "{n} active skills"),
    ]),
    ("and_os/etc/SYSTEM_MAP.md", [
        (r"\d+ Active Skills", "{n} Active Skills"),
    ]),
    ("and_os/etc/SYSTEM_ARCHITECTURE_GRAPH.md", [
        (r"\d+ Active Skills", "{n} Active Skills"),
    ]),
]


def project(vault_root: str, dry_run: bool = False) -> Dict[str, Any]:
    """Projects the on-disk skill count onto every carrier.

    Returns a report: {"count": int, "changed": [rel, ...], "skipped_missing":
    [rel, ...], "dry_run": bool}.
    """
    n = count_skills(vault_root)
    changed: List[str] = []
    missing: List[str] = []
    for rel, patterns in CARRIERS:
        path = os.path.join(vault_root, rel)
        if not os.path.exists(path):
            missing.append(rel)
            continue
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        new_text = text
        for pattern, template in patterns:
            new_text = re.sub(pattern, template.replace("{n}", str(n)), new_text)
        if new_text != text:
            if not dry_run:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(new_text)
            changed.append(rel)
    return {"count": n, "changed": changed, "skipped_missing": missing,
            "dry_run": dry_run}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Project the on-disk active-skills count onto all "
                    "manifest/doc carriers (idempotent; SSoT = disk)")
    parser.add_argument("--json", action="store_true", help="Machine-readable report")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report what would change without writing")
    args = parser.parse_args()

    report = project(VAULT_ROOT, dry_run=args.dry_run)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        verb = "would sync" if report["dry_run"] else "synced"
        print(f"skills on disk: {report['count']} | {verb}: "
              f"{', '.join(report['changed']) or 'no drift (idempotent no-op)'}")
        if report["skipped_missing"]:
            print(f"missing carriers (skipped): {', '.join(report['skipped_missing'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
