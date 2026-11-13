#!/usr/bin/env python3
"""
and_os/lib/vault/context.py — Unified navigation CONTEXT.md synchronization and link integrity engine.
Part of the monolithic and_os.lib.vault package.

Core Invariants:
  - Canonical note and directory listing standard.
  - Elimination of duplicate bullet list lines.
  - Correct markdown table delimiter handling.
"""

import os
import re
from typing import Dict, List, Set, Tuple

IGNORE_DIRS = {".space", ".obsidian", ".trash", "Trash", ".opencode", ".makemd", ".smart-env", ".git", "vault_shadow"}
IGNORE_FILES = {".DS_Store", "CONTEXT.md"}

def parse_context_links(context_file_path: str) -> Set[str]:
    """Extracts note basenames referenced in wikilinks within a CONTEXT.md file."""
    if not os.path.exists(context_file_path):
        return set()
    with open(context_file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    links = re.findall(r"\[\[([^\|\]]+)(?:\|[^\]]+)?\]\]", content)
    result = set()
    for l in links:
        clean = l.strip()
        if clean.endswith(".md"):
            clean = clean[:-3]
        base = os.path.basename(clean)
        result.add(base)
    return result

def sync_single_context(dir_path: str, fix: bool = True) -> Tuple[bool, List[str]]:
    """
    Synchronizes CONTEXT.md for a specific directory.
    Returns (is_up_to_date, list_of_missing_or_added_files).
    """
    context_file = os.path.join(dir_path, "CONTEXT.md")
    if not os.path.exists(context_file):
        return True, []

    existing_notes = []
    subdirs = []
    
    try:
        items = sorted(os.listdir(dir_path))
    except OSError:
        return True, []

    for item in items:
        if item in IGNORE_FILES or item.startswith('.'):
            continue
        p = os.path.join(dir_path, item)
        if os.path.isfile(p) and item.endswith('.md'):
            existing_notes.append(item)
        elif os.path.isdir(p) and item not in IGNORE_DIRS:
            subdirs.append(item)

    linked_names = parse_context_links(context_file)
    missing = [f for f in existing_notes if os.path.splitext(f)[0] not in linked_names and f not in linked_names]

    if not missing or not fix:
        return len(missing) == 0, missing

    # Insert missing files into note section
    with open(context_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_entries = [f"- [[{os.path.splitext(f)[0]}|{f}]] — auto-indexed\n" for f in missing]
    
    insert_idx = len(lines)
    for i, line in enumerate(lines):
        line_clean = line.strip().lower()
        if line_clean.startswith('---') and i > len(lines) - 10:
            insert_idx = i
            break
        elif 'навигация' in line_clean or 'ссылки' in line_clean or 'navigation' in line_clean:
            insert_idx = i
            break

    lines[insert_idx:insert_idx] = new_entries

    # Deduplicate consecutive lines
    deduped_lines = []
    prev_line = None
    for l in lines:
        if l.strip().startswith('- [[') and l == prev_line:
            continue
        deduped_lines.append(l)
        prev_line = l

    with open(context_file, "w", encoding="utf-8") as f:
        f.writelines(deduped_lines)

    return True, missing

def sync_all_contexts(vault_root: str, fix: bool = True) -> int:
    """Synchronizes all CONTEXT.md files across the vault."""
    updated_contexts = 0
    for root, dirs, files in os.walk(vault_root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]
        if "CONTEXT.md" in files:
            ok, diff = sync_single_context(root, fix=fix)
            if diff:
                updated_contexts += 1
    return updated_contexts
