#!/usr/bin/env python3
"""
and_os/lib/vault/graph.py — Markdown link graph management: wikilinks, cascade relocation, and orphan cleanup.
Part of the monolithic and_os.lib.vault package.

Core Invariants:
  - Robust regex parsing for [[target]] and [[target|alias]].
  - Support for media embeds ![[image.png]] and anchored links [[note#section]].
  - Atomic cascade refactoring of all incoming wikilinks when notes are relocated.
"""

import os
import re
from typing import Dict, List, Set, Tuple, Any

WIKILINK_REGEX = re.compile(r'(!?\[\[)([^\]]+)(\]\])')
IMG_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
IGNORE_DIRS = {".space", ".obsidian", ".trash", "Trash", ".opencode", ".makemd", ".smart-env", ".git", "vault_shadow"}

def scan_markdown_files(vault_root: str) -> List[str]:
    """Returns a list of all .md files within the vault excluding ignored directories."""
    md_files = []
    for root, dirs, files in os.walk(vault_root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]
        for f in files:
            if f.endswith('.md'):
                md_files.append(os.path.join(root, f))
    return md_files

def parse_wikilink_target(inner_text: str) -> Tuple[str, str, str]:
    """
    Parses the internal content of [[target#anchor|alias]].
    Returns (clean_target_path, anchor, alias).
    """
    raw = inner_text.replace(r'\|', '__ESCAPED_PIPE__')
    parts = raw.split('|')
    alias = parts[1].replace('__ESCAPED_PIPE__', '|') if len(parts) > 1 else ""
    target_part = parts[0].replace('__ESCAPED_PIPE__', '|').strip()
    
    anchor = ""
    if '#' in target_part:
        subparts = target_part.split('#', 1)
        target = subparts[0].strip()
        anchor = subparts[1].strip()
    else:
        target = target_part
        
    return target, anchor, alias

def cascade_rename_links(vault_root: str, old_rel_path: str, new_rel_path: str) -> int:
    """
    Cascades renaming across all incoming [[old_rel_path]] wikilinks in the vault to [[new_rel_path]].
    Supports full relative paths as well as bare basename wikilinks.
    Returns the count of updated files.
    """
    old_basename = os.path.basename(old_rel_path)
    old_name_no_ext, _ = os.path.splitext(old_basename)
    
    new_basename = os.path.basename(new_rel_path)
    new_name_no_ext, _ = os.path.splitext(new_basename)
    
    targets_to_replace = {
        old_rel_path,
        old_rel_path[:-3] if old_rel_path.endswith('.md') else old_rel_path,
        old_basename,
        old_name_no_ext
    }

    updated_files_count = 0
    all_md = scan_markdown_files(vault_root)
    
    for filepath in all_md:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            continue

        changed = False

        def _replace_link(match: Any) -> str:
            nonlocal changed
            prefix = match.group(1) # [[ or ![[
            inner = match.group(2)
            suffix = match.group(3) # ]]
            
            target, anchor, alias = parse_wikilink_target(inner)
            target_clean = target.rstrip('/')
            if target_clean in targets_to_replace:
                changed = True
                if '/' in target_clean:
                    new_target = new_rel_path[:-3] if new_rel_path.endswith('.md') else new_rel_path
                else:
                    new_target = new_name_no_ext

                new_inner = new_target
                if anchor:
                    new_inner += f"#{anchor}"
                if alias:
                    new_inner += f"|{alias}"
                return f"{prefix}{new_inner}{suffix}"
                
            return match.group(0)

        new_content = WIKILINK_REGEX.sub(_replace_link, content)
        if changed and new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            updated_files_count += 1

    return updated_files_count

def clean_broken_image_links(vault_root: str) -> int:
    """Normalizes missing image links into readable fallback placeholders."""
    existing_files = set()
    for root, dirs, files in os.walk(vault_root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]
        for f in files:
            existing_files.add(f)
            existing_files.add(os.path.relpath(os.path.join(root, f), vault_root))

    fixed_count = 0
    for filepath in scan_markdown_files(vault_root):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                c = f.read()
        except Exception:
            continue

        def _sub_img(m: Any) -> str:
            target = m.group(2).split('|')[0].strip()
            ext = os.path.splitext(target)[1].lower()
            if ext in IMG_EXTS and target not in existing_files and os.path.basename(target) not in existing_files:
                return f"[Image: {os.path.basename(target)}]"
            return m.group(0)

        new_c = WIKILINK_REGEX.sub(_sub_img, c)
        if new_c != c:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_c)
            fixed_count += 1

    return fixed_count
