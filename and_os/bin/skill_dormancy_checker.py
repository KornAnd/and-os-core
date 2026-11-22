#!/usr/bin/env python3
"""
Skill Usage & Dormancy Analyzer
AnD os v1.2.0 - Skill Governance (Rule №18)

Parses and_os/lib/skills/telemetry.md, matches against all registered skills,
and identifies active vs dormant skills (> 60 days unused).
"""

import os
import re
from datetime import datetime, date
from pathlib import Path

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../.."))
TELEMETRY_PATH = os.path.join(VAULT_ROOT, "and_os/lib/skills/telemetry.md")
SKILLS_DIR = os.path.join(VAULT_ROOT, "and_os/lib/skills")

# 18.11 R8 (F8): the dot belongs in the token class — without it a
# "sys.audit" token truncated to "sys", and the two-way substring match
# below credited every sys.* facade row to every skill whose name
# contains "sys" (system-audit/system-architect showed 2 274 phantom
# calls each).
LINE_PATTERN = re.compile(r"^-\s+(\d{4}-\d{2}-\d{2})\s+\|\s+\w+\s+\|\s+([a-zA-Z0-9_.\-\/]+)")

def _scan_file(path: str, all_skills: list, usage_map: dict, seen: set = None) -> None:
    """Parse one telemetry journal (live or monthly archive) and merge usage dates.

    When a shared `seen` set is passed, exact-duplicate lines (journal
    entries present in more than one source) are counted once.
    """
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            m = LINE_PATTERN.match(line.strip())
            if not m:
                continue
            if seen is not None:
                key = line.strip()
                if key in seen:
                    continue
                seen.add(key)
            try:
                dt = datetime.strptime(m.group(1), "%Y-%m-%d").date()
            except ValueError:
                continue
            # Match sub-skills or compound tokens
            for s in all_skills:
                if s in m.group(2) or m.group(2) in s:
                    usage_map[s].append(dt)

def analyze_skill_dormancy(dormant_days_threshold: int = 60) -> dict:
    """Analyzes telemetry for skill usage frequency and dormancy.

    Scans the live journal (and_os/lib/skills/telemetry.md) PLUS the monthly
    archives (and_os/var/telemetry_archive_YYYYMM.md, Rule #72) so compaction
    does not blind the Rule #18 governance report (18.11 fix).
    """
    all_skills = []
    if os.path.exists(SKILLS_DIR):
        for entry in os.listdir(SKILLS_DIR):
            skill_md = os.path.join(SKILLS_DIR, entry, "SKILL.md")
            if os.path.isdir(os.path.join(SKILLS_DIR, entry)) and os.path.exists(skill_md):
                all_skills.append(entry)

    usage_map = {s: [] for s in all_skills}

    # Parse the live journal + all monthly archives (Rule #72 relocation)
    # + the legacy pre-#72 archive that still lives next to the live
    # journal (18.11 R8: without it the report is blind to the oldest
    # history). Exact-duplicate lines across sources count once.
    scanned = []
    if os.path.exists(TELEMETRY_PATH):
        scanned.append(TELEMETRY_PATH)
    var_dir = os.path.join(VAULT_ROOT, "and_os", "var")
    if os.path.isdir(var_dir):
        scanned.extend(sorted(Path(var_dir).glob("telemetry_archive_*.md")))
    scanned.extend(sorted(Path(SKILLS_DIR).glob("telemetry_archive_*.md")))
    seen = set()
    for p in scanned:
        _scan_file(str(p), all_skills, usage_map, seen)
                            
    today = date.today()  # live anchor (18.11 fix: was hardcoded 2026-10-01,
                          # produced negative days_ago and a frozen report date)
    
    active_skills = []
    dormant_skills = []
    never_logged_skills = []
    
    for s, dates in usage_map.items():
        if not dates:
            never_logged_skills.append(s)
        else:
            last_used = max(dates)
            days_ago = (today - last_used).days
            item = {"skill": s, "last_used": str(last_used), "days_ago": days_ago, "call_count": len(dates)}
            if days_ago > dormant_days_threshold:
                dormant_skills.append(item)
            else:
                active_skills.append(item)
                
    dormant_skills.sort(key=lambda x: x["days_ago"], reverse=True)
    active_skills.sort(key=lambda x: x["call_count"], reverse=True)
    
    return {
        "today": str(today),
        "scanned_sources": len(scanned),
        "total_skills": len(all_skills),
        "active_count": len(active_skills),
        "dormant_count": len(dormant_skills),
        "never_logged_count": len(never_logged_skills),
        "active_skills": active_skills,
        "dormant_skills": dormant_skills,
        "never_logged_skills": sorted(never_logged_skills)
    }

def print_dormancy_report(res: dict) -> None:
    print("=" * 65)
    print(f"📊 SKILL GOVERNANCE REPORT (Threshold: 60 days) - {res['today']}")
    print(f"Sources: {res.get('scanned_sources', 1)} journal file(s) (live + monthly archives)")
    print("=" * 65)
    print(f"Total Skills Registered : {res['total_skills']}")
    print(f"Active in last 60 days  : {res['active_count']}")
    print(f"Dormant (>60 days)      : {res['dormant_count']}")
    print(f"Never explicitly logged : {res['never_logged_count']}")
    print("-" * 65)
    print("🔥 TOP ACTIVE SKILLS:")
    for a in res["active_skills"][:8]:
        print(f"  - {a['skill']:<25} : {a['call_count']} calls (last: {a['last_used']}, {a['days_ago']}d ago)")
        
    print("-" * 65)
    print("💤 DORMANT SKILLS (Review for standby/archive per Rule №18):")
    for d in res["dormant_skills"]:
        print(f"  - {d['skill']:<25} : {d['days_ago']} days since last call ({d['last_used']})")
    print("=" * 65)

if __name__ == "__main__":
    report = analyze_skill_dormancy()
    print_dormancy_report(report)
