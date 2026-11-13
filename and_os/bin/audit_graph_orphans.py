#!/usr/bin/env python3
"""
audit_graph_orphans.py — Precise graph-connectivity scanner of the Obsidian Vault.
Finds files that appear as orphans in the Obsidian visual graph:
1. Have 0 incoming links from visible .md files (excluding ignored CONTEXT.md)
2. Have 0 outgoing links to visible .md files (or only backlinks to the hidden CONTEXT.md)
"""

import os
import sys
import re
import json
from collections import defaultdict

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
IGNORE_DIRS = {".space", ".obsidian", ".trash", "Trash", ".opencode", ".makemd", ".smart-env", ".git", "node_modules", ".cache", "repo"}
IGNORE_FILES = {".DS_Store"}

# Files that Obsidian hides via userIgnoreFilters in app.json
HIDDEN_FROM_GRAPH = {"CONTEXT.md", "context_export.md", "context_lite.md"}

def is_hidden_file(filename):
    bn = os.path.basename(filename)
    if bn in HIDDEN_FROM_GRAPH or bn.startswith("context_"):
        return True
    return False

import unicodedata

def extract_wikilinks(content):
    # [[target|alias]] or [[target]]
    matches = re.findall(r"\[\[([^\|\]\r\n]+)(?:\|[^\]\r\n]+)?\]\]", content)
    links = []
    for m in matches:
        clean = unicodedata.normalize('NFC', m.strip())
        if clean.endswith(".md"):
            clean = clean[:-3]
        links.append(clean)
    return links

def main():
    all_files = {} # rel_path -> { "basename": str, "name_no_ext": str, "outgoing": list }
    
    for root, dirs, files in os.walk(VAULT_ROOT):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in files:
            if not f.endswith(".md") or f in IGNORE_FILES:
                continue
            full_path = os.path.join(root, f)
            rel_path = unicodedata.normalize('NFC', os.path.relpath(full_path, VAULT_ROOT))
            
            # Files hidden from the graph are not counted as nodes
            if is_hidden_file(rel_path):
                continue
                
            bn = unicodedata.normalize('NFC', os.path.basename(rel_path))
            name_no_ext = bn[:-3]
            
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
                outgoing = extract_wikilinks(content)
            except Exception:
                outgoing = []
                
            all_files[rel_path] = {
                "full_path": full_path,
                "basename": bn,
                "name_no_ext": name_no_ext,
                "outgoing": outgoing
            }

    # Build the incoming-links matrix
    # A link may point by relative path (Folder/Name) or purely by basename (Name)
    in_degree = defaultdict(int)
    out_degree_visible = defaultdict(int)

    # Fast index of file names
    basename_map = defaultdict(list)
    for rel_path, data in all_files.items():
        basename_map[data["name_no_ext"]].append(rel_path)
        basename_map[data["basename"]].append(rel_path)
        basename_map[rel_path].append(rel_path)
        if rel_path.endswith(".md"):
            basename_map[rel_path[:-3]].append(rel_path)

    for src_rel, data in all_files.items():
        for target in data["outgoing"]:
            # Check whether the link points to an existing visible file
            target_clean = os.path.basename(target)
            if target in basename_map or target_clean in basename_map:
                # Found a valid target in the graph
                target_paths = basename_map.get(target) or basename_map.get(target_clean)
                for tp in target_paths:
                    if tp != src_rel: # self-loops are not counted
                        in_degree[tp] += 1
                        out_degree_visible[src_rel] += 1

    # Orphans in Obsidian terms:
    # A graph node is isolated if in_degree == 0 AND out_degree == 0 (no visible edge at all)
    isolated_orphans = []
    # Weakly linked: 0 incoming (input dead-end, nobody links to it)
    zero_in = []

    for rel_path, data in all_files.items():
        in_c = in_degree[rel_path]
        out_c = out_degree_visible[rel_path]
        if in_c == 0 and out_c == 0:
            isolated_orphans.append((rel_path, in_c, out_c))
        elif in_c == 0:
            zero_in.append((rel_path, in_c, out_c))

    print(f"📊 Total visible Markdown files in the graph: {len(all_files)}")
    print(f"🔴 Fully isolated orphans (0 incoming, 0 outgoing): {len(isolated_orphans)}")
    print(f"🟡 One-way notes (0 incoming, but have outgoing): {len(zero_in)}")

    # Group isolated orphans by root directories
    by_folder = defaultdict(list)
    for p, inc, outc in isolated_orphans:
        root_folder = p.split(os.sep)[0]
        by_folder[root_folder].append(p)

    print("\n📂 Distribution of isolated orphans by directory:")
    for folder, files in sorted(by_folder.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  • {folder}/ : {len(files)} orphans")

    # Save the report for further work
    report_file = os.path.join(VAULT_ROOT, "and_os/var/graph_orphans_report.json")
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as rf:
        json.dump({
            "total_visible": len(all_files),
            "isolated_count": len(isolated_orphans),
            "zero_in_count": len(zero_in),
            "isolated_by_folder": {k: len(v) for k, v in by_folder.items()},
            "isolated_files": [p for p, _, _ in isolated_orphans]
        }, rf, ensure_ascii=False, indent=2)

    print(f"\n💾 Full report saved: and_os/var/graph_orphans_report.json")

if __name__ == "__main__":
    main()
