#!/usr/bin/env python3
"""
link_graph_orphans.py — Idempotent attachment of isolated notes to the root and category hubs of Obsidian.

Goal:
1. For each isolated note (orphan), determine the nearest hub visible in the graph.
2. Safely add the navigation footer (a backlink) to the end of the file (if it is not there).
3. Add a direct link to the note in the parent index/hub (if absent),
   ensuring 100% connectivity and clustering in the Obsidian Force-Directed graph.
"""

import os
import sys
import json
import re
from pathlib import Path

try:
    from and_os.lib.core.root_config import RootConfig
    VAULT_ROOT = Path(RootConfig.load().vault_root)
except Exception:
    VAULT_ROOT = Path(__file__).resolve().parents[2]
ORPHANS_REPORT = VAULT_ROOT / "and_os/var/graph_orphans_report.json"

DOMAIN_HUBS = {
    "Clippings": "Clippings/Clippings.md",
    "Book": "Book/Book.md",
    "Story": "Story/Story.md",
    "Studio": "Studio/Studio.md",
    "Product": "Product/Product.md",
    "Ta-Bu": "Ta-Bu/Ta-Bu.md",
    "CG_core": "CG_core/CG_core.md",
    "Tags": "Tags/Tags.md",
    "Tasks": "Tasks/Tasks.md",
    "Industry": "Industry/Industry.md",
    "Nero": "Nero/Nero.md",
}

def find_target_hub(rel_path: str) -> tuple[str, str]:
    """
    Determines the most relevant visible hub for the note.
    Returns (hub_rel_path, hub_name).
    """
    parts = Path(rel_path).parts
    if len(parts) <= 1:
        return "Vault.md", "Vault"
    
    domain = parts[0]
    
    # 1. Check the nested hubs for Clippings (e.g. Clippings/<category>/<category>.md)
    if domain == "Clippings" and len(parts) >= 3:
        cat_folder = parts[1]
        cat_hub = f"Clippings/{cat_folder}/{cat_folder}.md"
        if (VAULT_ROOT / cat_hub).exists():
            return cat_hub, cat_folder
        return "Clippings/Clippings.md", "Clippings"
        
    # 2. Check the Nero subfolders
    if domain == "Nero":
        if len(parts) >= 3:
            sub = parts[1]
            # Check for the presence of a special hub
            if sub == "skills":
                return "and_os/lib/skills/README.md", "Skills Registry"
            if sub == "core":
                return "Nero/core/CORE.md", "Nero Core" if (VAULT_ROOT / "Nero/core/CORE.md").exists() else ("Nero/Nero.md", "Nero")
            if sub == "ai":
                return "and_os/etc/SYSTEM_MAP.md", "SYSTEM MAP" if (VAULT_ROOT / "and_os/etc/SYSTEM_MAP.md").exists() else ("Nero/Nero.md", "Nero")
        return "Nero/Nero.md", "Nero"

    # 3. Standard domain hubs
    if domain in DOMAIN_HUBS:
        hub_path = DOMAIN_HUBS[domain]
        if (VAULT_ROOT / hub_path).exists():
            return hub_path, domain
            
    # Default fallback
    return "Vault.md", "Vault"

def safe_append_backlink(file_path: Path, hub_wikilink: str, hub_title: str) -> bool:
    """Safely appends a backlink to the end of the file."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False

    link_target = hub_wikilink.replace(".md", "")
    # Check whether the file already contains a link to this hub
    if f"[[{link_target}" in content or f"[[{Path(link_target).name}" in content:
        return False

    # Build a clean footer
    footer = f"\n\n---\n[[{link_target}|← {hub_title}]]\n"
    
    # Write
    new_content = content.rstrip() + footer
    file_path.write_text(new_content, encoding="utf-8")
    return True

def safe_add_link_to_hub(hub_file: Path, target_rel_path: str, target_name: str) -> bool:
    """Adds a link to the note in the parent hub if it is not there."""
    if not hub_file.exists():
        return False
        
    try:
        content = hub_file.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading hub {hub_file}: {e}")
        return False
        
    target_link = target_rel_path.replace(".md", "")
    target_base = Path(target_link).name
    
    # Check whether the link exists in the hub
    if f"[[{target_link}" in content or f"[[{target_base}" in content:
        return False
        
    # Add the link to the end of the hub under the related-notes heading or simply into the list
    entry = f"- [[{target_link}|{target_base}]]\n"
    
    if "## Ссылки" in content or "## Связанные заметки" in content or "## Файлы" in content:
        # Add it to the existing section
        section_pattern = r"(##\s+(?:Ссылки|Связанные заметки|Файлы)[\s\S]*?)(\n##|\Z)"
        match = re.search(section_pattern, content)
        if match:
            new_section = match.group(1).rstrip() + "\n" + entry
            content = content[:match.start()] + new_section + content[match.end()-len(match.group(2)):]
        else:
            content = content.rstrip() + f"\n\n## Связанные материалы\n{entry}"
    else:
        content = content.rstrip() + f"\n\n## Связанные материалы\n{entry}"
        
    hub_file.write_text(content, encoding="utf-8")
    return True

def main():
    if not ORPHANS_REPORT.exists():
        print(f"Report not found: {ORPHANS_REPORT}")
        sys.exit(1)
        
    with open(ORPHANS_REPORT, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    orphans = data.get("isolated_files", [])
    print(f"Loaded {len(orphans)} isolated files to process.")
    
    linked_count = 0
    hub_updated_count = 0
    
    for rel_path in orphans:
        p = VAULT_ROOT / rel_path
        if not p.exists():
            continue
            
        hub_rel, hub_title = find_target_hub(rel_path)
        hub_path = VAULT_ROOT / hub_rel
        
        # 1. Add the backlink footer to the orphan note
        if safe_append_backlink(p, hub_rel, hub_title):
            linked_count += 1
            
        # 2. Add the link to the parent hub
        if safe_add_link_to_hub(hub_path, rel_path, p.stem):
            hub_updated_count += 1
            
    print(f"Summary:")
    print(f"- Notes linked with footer: {linked_count}")
    print(f"- Hub mentions added: {hub_updated_count}")

if __name__ == "__main__":
    main()
