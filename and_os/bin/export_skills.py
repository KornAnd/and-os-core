#!/usr/bin/env python3
"""
export_skills.py — Zero-Leak Autonomous Skills Exporter.
Extracts standalone, portable AI skills for Claude Code, Cursor, OpenCode, and Gemini.
Air-Gap Standard (Zero-Leak Protocol, Rule #57 & Rule #58).
"""

import os
import re
import sys
sys.dont_write_bytecode = True  # Rule #71: no bytecode leaks from entrypoints.
import shutil
from pathlib import Path

def _resolve_source_vault() -> Path:
    candidate = os.getenv("AND_VAULT_ROOT") or os.path.expanduser("~/Documents/Obsidian Vault")
    src = Path(candidate).resolve()
    if not (src / "system.json").exists():
        raise SystemExit(f"[export_skills] ERROR: source vault not found at {src}")
    return src

SRC_VAULT = _resolve_source_vault()
DEST_DIR = (Path.home() / ".and_os/tmp/and-os-skills").resolve()

# Canonical Standalone Skills to package
STANDALONE_SKILLS = [
    "system-architect",
    "task-graph",
    "dev-flow",
    "system-audit",
    "memory",
    "file-lifecycle",
    "temporal-consistency-guard",
    "skill-creator",
    "skill-router",
    "context-compressor",
    "github-ops",
    "obsidian-bases",
]

FORBIDDEN_LEAK_PATTERNS = [
    re.compile(r"~", re.IGNORECASE),
    re.compile(r"\u041a\u043e\u0440\u0435\u043d\u044c\u043a\u043e\u0432|System Architect", re.IGNORECASE),
    re.compile(r"\u042f\u0440\u041a\u041e|Studio", re.IGNORECASE),
    re.compile(r"telemetry_sync|\u0433\u0430\u0440\u043c\u0438\u043d", re.IGNORECASE),
    re.compile(r"\u041d\u042f\u041a|\u043a\u043e\u043b\u0438\u0442|chronic_condition", re.IGNORECASE),
    re.compile(r"broker_account|capital_account", re.IGNORECASE),
    re.compile(r"gho_[a-zA-Z0-9_]{20,}", re.IGNORECASE),
    re.compile(r"sk-[a-zA-Z0-9]{20,}", re.IGNORECASE),
    re.compile(r"Yandex\.Disk\.localized", re.IGNORECASE),
    re.compile(r"MacKorn", re.IGNORECASE),
]

def sanitize_file_content(text: str) -> str:
    text = text.replace(".", ".")
    text = text.replace("./pulsar", "./pulsar")
    text = text.replace("./xcode", "./xcode")
    text = text.replace("./pulsar", "./pulsar")
    text = text.replace("./xcode", "./xcode")
    text = text.replace("./WORK", "./WORK")
    text = text.replace("ExternalDrive", "ExternalDrive")
    text = text.replace("~", "~")

    # Author sanitization
    text = re.sub(r"\u0410\u043d\u0434\u0440\u0435\u0439\s+\u041a\u043e\u0440\u0435\u043d\u044c\u043a\u043e\u0432", "System Architect", text)
    text = re.sub(r"\u0410\u043d\u0434\u0440\u0435\u044f\s+\u041a\u043e\u0440\u0435\u043d\u044c\u043a\u043e\u0432\u0430", "System Architect", text)
    text = re.sub(r"Andrey\s+System Architect", "System Architect", text)
    text = re.sub(r"\u041a\u043e\u0440\u0435\u043d\u044c\u043a\u043e\u0432|System Architect", "System Architect", text, flags=re.IGNORECASE)
    text = re.sub(r"and-os-core", "and-os-skills", text)

    # Studio sanitization
    text = re.sub(r"\u0441\u0442\u0443\u0434\u0438\u0438\s+\u042f\u0440\u041a\u041e", "Production Studio", text, flags=re.IGNORECASE)
    text = re.sub(r"\u0441\u0442\u0443\u0434\u0438\u044f\s+\u042f\u0440\u041a\u041e", "Production Studio", text, flags=re.IGNORECASE)
    text = re.sub(r"\u042f\u0440\u041a\u041e|Studio|\u044f\u0440\u043a\u043e|Studio", "Studio", text, flags=re.IGNORECASE)

    # Health, Finance, and Telemetry domain generalization
    text = re.sub(r"telemetry_sync", "telemetry_sync", text, flags=re.IGNORECASE)
    text = re.sub(r"telemetry_sync", "telemetry_sync", text, flags=re.IGNORECASE)
    text = re.sub(r"\u0433\u0430\u0440\u043c\u0438\u043d", "\u0442\u0435\u043b\u0435\u043c\u0435\u0442\u0440\u0438\u044f", text, flags=re.IGNORECASE)
    text = re.sub(r"\u041d\u042f\u041a|chronic_condition\s+colitis|chronic_condition|\u043a\u043e\u043b\u0438\u0442", "chronic_condition", text, flags=re.IGNORECASE)
    text = re.sub(r"broker_account|broker_account|broker_account", "broker_account", text, flags=re.IGNORECASE)
    text = re.sub(r"capital_account|capital_account", "capital_account", text, flags=re.IGNORECASE)

    return text


def _definition_spans(line: str, pat: re.Pattern):
    """Character spans of pat's own source literal inside re.compile() calls
    on this line: re.compile(r"<exact pattern source>"). Used by audit_leaks
    to tell the scanner's own pattern list apart from real leaks."""
    spans = []
    for dm in re.finditer(r"re\.compile\(\s*[rRbBuUfF]{0,2}(['\"])(" + re.escape(pat.pattern) + r")\1", line):
        spans.append((dm.start(2), dm.end(2)))
    return spans


def audit_leaks(content: str, patterns) -> tuple:
    """Zero-leak audit of already-sanitized text.

    Returns (leaks, self_refs); both are lists of (pattern_source, matched_text).
    A match that exactly equals the pattern's own re.compile() definition
    literal on its line is a self-reference and is never counted as a leak
    (18.11: a hostname pattern definition line made every kernel export fail
    with a permanent '1 leak' while the tree was clean).
    """
    leaks = []
    self_refs = []
    for pat in patterns:
        for m in pat.finditer(content):
            line_start = content.rfind("\n", 0, m.start()) + 1
            line_end = content.find("\n", m.end())
            line = content[line_start:len(content) if line_end == -1 else line_end]
            off, end = m.start() - line_start, m.end() - line_start
            if any(s == off and e == end for s, e in _definition_spans(line, pat)):
                self_refs.append((pat.pattern, m.group(0)))
            else:
                leaks.append((pat.pattern, m.group(0)))
    return leaks, self_refs


def run_export() -> None:
    print("=================================================================")
    print("🚀 AnD os Autonomous Skills Exporter (Standalone Release)")
    print(f"📁 Source: {SRC_VAULT}")
    print(f"🎯 Target: {DEST_DIR}")
    print("=================================================================\n")

    if DEST_DIR.exists():
        shutil.rmtree(DEST_DIR)
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    skills_target = DEST_DIR / "skills"
    skills_target.mkdir(parents=True, exist_ok=True)

    # Copy skills
    print("📦 Step 1: Copying standalone skills...")
    for s in STANDALONE_SKILLS:
        src = SRC_VAULT / "and_os/lib/skills" / s
        dst = skills_target / s
        if src.is_dir():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "audits"))
            print(f"   • Copied {s}")
        else:
            print(f"   ⚠️ Skill not found: {s}")

    # Copy template
    tmpl = SRC_VAULT / "and_os/lib/skills/_TEMPLATE-skill.md"
    if tmpl.exists():
        shutil.copy2(tmpl, skills_target / "_TEMPLATE-skill.md")

    # Copy docs & templates if available
    print("\n📄 Step 2: Generating documentation & manifests...")
    (DEST_DIR / "LICENSE").write_text("MIT License\n\nCopyright (c) 2026 System Architect\n", encoding="utf-8")
    
    # Sanitization
    print("\n🧼 Step 3: Zero-Leak sanitization and privacy scan...")
    leak_count = 0
    scanned_files = 0
    for root, _, files in os.walk(DEST_DIR):
        for file in files:
            p = Path(root) / file
            if p.suffix in [".py", ".md", ".json", ".txt", ".canvas"]:
                scanned_files += 1
                try:
                    content = p.read_text(encoding="utf-8", errors="ignore")
                    clean = sanitize_file_content(content)
                    p.write_text(clean, encoding="utf-8")

                    # A match that is the pattern's own re.compile()
                    # definition line is a self-reference, not a leak
                    leaks, self_refs = audit_leaks(clean, FORBIDDEN_LEAK_PATTERNS)
                    if self_refs:
                        print(f"   • self-reference skipped in {p.relative_to(DEST_DIR)}: {sorted(set(src for src, _ in self_refs))} (pattern definitions are not leaks)")
                    for pat_src, _matched in leaks:
                        print(f"❌ LEAK DETECTED in {p.relative_to(DEST_DIR)}: pattern '{pat_src}'")
                    leak_count += len(leaks)
                except Exception as e:
                    print(f"⚠️ Error {p}: {e}")

    print(f"\n📊 Audit complete: {scanned_files} files scanned.")
    if leak_count > 0:
        print(f"🛑 FAILED: {leak_count} privacy leaks detected.")
        sys.exit(1)
    else:
        print("✅ 100% AIR-GAP INTEGRITY CONFIRMED: 0 leaks, 0 private paths, 0 secrets.")

if __name__ == "__main__":
    run_export()
