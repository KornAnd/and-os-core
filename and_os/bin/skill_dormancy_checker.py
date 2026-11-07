#!/usr/bin/env python3
"""
Skill Usage & Dormancy Analyzer
AnD os v8.1 - Skill Governance (Rule №18)

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

def analyze_skill_dormancy(dormant_days_threshold: int = 60) -> dict:
    """Analyzes telemetry for skill usage frequency and dormancy."""
    all_skills = []
    if os.path.exists(SKILLS_DIR):
        for entry in os.listdir(SKILLS_DIR):
            skill_md = os.path.join(SKILLS_DIR, entry, "SKILL.md")
            if os.path.isdir(os.path.join(SKILLS_DIR, entry)) and os.path.exists(skill_md):
                all_skills.append(entry)
                
    usage_map = {s: [] for s in all_skills}
    
    # Parse telemetry
    if os.path.exists(TELEMETRY_PATH):
        date_pattern = re.compile(r"^-\s+(\d{4}-\d{2}-\d{2})\s+\|\s+\w+\s+\|\s+([a-zA-Z0-9_\-\/]+)")
        with open(TELEMETRY_PATH, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                m = date_pattern.match(line.strip())
                if m:
                    dt_str, skill_token = m.group(1), m.group(2)
                    try:
                        dt = datetime.strptime(dt_str, "%Y-%m-%d").date()
                    except Exception:
                        continue
                    # Match sub-skills or compound tokens
                    for s in all_skills:
                        if s in skill_token or skill_token in s:
                            usage_map[s].append(dt)
                            
    today = date(2026, 10, 1) # local current date anchor
    
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
        "total_skills": len(all_skills),
        "active_count": len(active_skills),
        "dormant_count": len(dormant_skills),
        "never_logged_count": len(never_logged_skills),
        "active_skills": active_skills,
        "dormant_skills": dormant_skills,
        "never_logged_skills": sorted(never_logged_skills)
    }

def print_dormancy_report(res: dict):
    print("=" * 65)
    print(f"📊 SKILL GOVERNANCE REPORT (Threshold: 60 days) - {res['today']}")
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
