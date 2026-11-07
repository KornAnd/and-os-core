#!/usr/bin/env python3
"""
comfy_node_registry.py — Active ComfyUI Node Version Registry & Validator (Rule #45 & Update Guard).
Principles: Think in Code (Rule #16), 100% Zero-Cost Policy (Rule #45),
Automatic node compatibility verification during ComfyUI updates (Node Compatibility & Regression Guard).

Capabilities:
  1. Scan all workflows (Vault + ComfyUI user workflows) for utilized node classes.
  2. Cross-reference with global ComfyUI node database (Core + ComfyUI-Manager extension map).
  3. Identify local custom node packages (chbs_nodes, etc.).
  4. Build version database and documentation in `and_os/lib/workflows/comfy/comfy_nodes_registry.md` and `.json`.
  5. Verify node compatibility before/after ComfyUI updates (`--verify`).

Usage:
  python3 comfy_node_registry.py --scan               # Full workflow scan and node database build
  python3 comfy_node_registry.py --verify [wf.json]   # Verify node compatibility
  python3 comfy_node_registry.py --json               # Output node registry in JSON format
"""

import os
import sys
import glob
import json
import argparse
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
OUTPUT_JSON = os.path.join(VAULT_ROOT, "and_os/lib/workflows/comfy/comfy_nodes_registry.json")
OUTPUT_MD = os.path.join(VAULT_ROOT, "and_os/lib/workflows/comfy/comfy_nodes_registry.md")
PROC_DIR = os.path.join(VAULT_ROOT, "and_os/proc")

# ComfyUI installation candidate directories
COMFY_DIRS = [
    os.path.expanduser("~/Documents/ComfyUI"),
    os.path.expanduser("~/ComfyUI-Installs/ComfyUI/ComfyUI")
]

EXTENSION_MAP_PATHS = [
    os.path.expanduser("~/Documents/ComfyUI/.venv/lib/python3.12/site-packages/comfyui_manager/extension-node-map.json"),
    os.path.expanduser("~/Documents/ComfyUI/custom_nodes/ComfyUI-Manager/extension-node-map.json")
]

LOCAL_CUSTOM_NODES_DIR = os.path.expanduser("~/Documents/ComfyUI/custom_nodes")

def _parse_extension_map_payload(ext_map: Dict[str, Any]) -> Dict[str, List[str]]:
    """Inverts extension-node-map from repo -> nodes to node -> repos."""
    node_to_ext: Dict[str, List[str]] = {}
    for repo, item in ext_map.items():
        if not (isinstance(item, list) and len(item) > 0 and isinstance(item[0], list)):
            continue
        for n in item[0]:
            if n not in node_to_ext:
                node_to_ext[n] = []
            node_to_ext[n].append(repo)
    return node_to_ext

def load_extension_map() -> Dict[str, List[str]]:
    """Load global ComfyUI node-to-extension mapping."""
    for p in EXTENSION_MAP_PATHS:
        if not os.path.exists(p):
            continue
        try:
            with open(p, "r", encoding="utf-8") as f:
                ext_map = json.load(f)
            return _parse_extension_map_payload(ext_map)
        except (json.JSONDecodeError, OSError) as err:
            sys.stderr.write(f"[comfy_registry] Warning: invalid ext map {p}: {err}\n")
    return {}

def scan_local_custom_nodes():
    """Scan custom node packages in local custom_nodes directory."""
    custom_nodes = {}
    if os.path.exists(LOCAL_CUSTOM_NODES_DIR):
        for entry in os.listdir(LOCAL_CUSTOM_NODES_DIR):
            pkg_path = os.path.join(LOCAL_CUSTOM_NODES_DIR, entry)
            if os.path.isdir(pkg_path) and not entry.startswith("."):
                init_py = os.path.join(pkg_path, "__init__.py")
                if os.path.exists(init_py):
                    try:
                        with open(init_py, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        if "NODE_CLASS_MAPPINGS" in content:
                            custom_nodes[entry] = pkg_path
                    except OSError as init_err:
                        sys.stderr.write(f"[comfy_registry] Warning reading {init_py}: {init_err}\n")
    return custom_nodes

def collect_all_workflows():
    """Collect all workflow JSON files across the Vault and ComfyUI user directories."""
    workflows = []
    
    # 1. Vault workflows
    for root, dirs, files in os.walk(VAULT_ROOT):
        dirs[:] = [d for d in dirs if d not in {".space", ".obsidian", ".trash", "Trash", ".opencode", "node_modules", ".git"}]
        for f in files:
            if f.endswith(".json"):
                full_p = os.path.join(root, f)
                try:
                    with open(full_p, "r", encoding="utf-8", errors="ignore") as jf:
                        d = json.load(jf)
                    if isinstance(d, dict) and ("nodes" in d or any(isinstance(v, dict) and "class_type" in v for v in d.values())):
                        workflows.append(full_p)
                except (json.JSONDecodeError, OSError):
                    # Skip non-workflow or unreadable JSON silently
                    continue

    # 2. ComfyUI User workflows
    user_wf_dir = os.path.expanduser("~/Documents/ComfyUI/user/default/workflows")
    if os.path.exists(user_wf_dir):
        for f in glob.glob(os.path.join(user_wf_dir, "*.json")):
            if f not in workflows:
                workflows.append(f)
                
    return sorted(list(set(workflows)))

def extract_nodes_from_workflow(file_path):
    """Extract list of referenced node classes from a workflow JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            d = json.load(f)
    except Exception:
        return []

    node_types = []
    if isinstance(d, dict):
        if "nodes" in d and isinstance(d["nodes"], list):
            for n in d["nodes"]:
                if isinstance(n, dict) and "type" in n and n["type"]:
                    node_types.append(n["type"])
        else:
            # API prompt format
            for v in d.values():
                if isinstance(v, dict) and "class_type" in v and v["class_type"]:
                    node_types.append(v["class_type"])
    return node_types

def build_registry():
    """Build complete node usage registry and persist to Markdown and JSON."""
    ext_map = load_extension_map()
    local_custom_pkgs = scan_local_custom_nodes()
    workflows = collect_all_workflows()

    registry = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_workflows": len(workflows),
        "total_distinct_nodes": 0,
        "nodes": {},
        "packages": {}
    }

    node_usage = {}
    for wf in workflows:
        rel_wf = os.path.relpath(wf, VAULT_ROOT) if wf.startswith(VAULT_ROOT) else f"~/Documents/ComfyUI/.../{os.path.basename(wf)}"
        nodes = extract_nodes_from_workflow(wf)
        for n in nodes:
            if n not in node_usage:
                node_usage[n] = set()
            node_usage[n].add(rel_wf)

    registry["total_distinct_nodes"] = len(node_usage)

    # Classify each node
    for n, wfs in node_usage.items():
        exts = ext_map.get(n, [])
        is_core = "https://github.com/comfyanonymous/ComfyUI" in exts
        
        if is_core:
            source = "ComfyUI Core (Built-in)"
            repo = "https://github.com/comfyanonymous/ComfyUI"
            stability = "HIGH (Core API)"
        elif n.startswith("CHBS_"):
            source = "Local Custom Package (chbs_nodes)"
            repo = "local://custom_nodes/chbs_nodes"
            stability = "CONTROLLED (Internal Pipeline)"
        elif len(exts) > 0:
            source = "External Custom Node (ComfyUI-Manager)"
            repo = exts[0]
            stability = "REQUIRES_VERIFICATION"
        else:
            source = "User Macro / Built-in Extension Node"
            repo = "N/A"
            stability = "VERIFY"

        registry["nodes"][n] = {
            "type": n,
            "source": source,
            "repository": repo,
            "stability_rating": stability,
            "used_in_workflows_count": len(wfs),
            "workflows": sorted(list(wfs))
        }

    # Persist JSON
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)

    # Persist Markdown
    md_content = f"""---
tags:
  - comfyui
  - nodes
  - registry
  - production
updated: {registry['updated_at']}
---

# ComfyUI Node Version & Usage Registry

> **Purpose:** Active registry of used ComfyUI nodes to prevent regression during updates (Rule #45 & Update Guard).
> **Total Distinct Node Types:** {len(node_usage)} | **Scanned Workflows:** {len(workflows)}
> **Verification Command:** `python3 and_os/bin/comfy_node_registry.py --verify`

---

## 1. Stability Category Summary

| Source Category | Node Count | Update Regression Risk |
| :--- | :---: | :--- |
| **ComfyUI Core (Official)** | {sum(1 for v in registry['nodes'].values() if 'Core' in v['source'])} | Minimal (official backwards compatibility) |
| **Local Custom Nodes (CHBS/Nero)** | {sum(1 for v in registry['nodes'].values() if 'Local' in v['source'])} | Zero (controlled in internal repository) |
| **External Extensions (Community Nodes)** | {sum(1 for v in registry['nodes'].values() if 'External' in v['source'])} | Medium (requires manager verification / git pull) |
| **Other / UI Macros** | {sum(1 for v in registry['nodes'].values() if 'User Macro' in v['source'])} | Low |

---

## 2. Complete Node Registry & Project Usages

| Node Type | Source / Repository | Stability | Workflow Count | Usage Examples |
| :--- | :--- | :---: | :---: | :--- |
"""
    for n in sorted(registry["nodes"].keys()):
        item = registry["nodes"][n]
        repo_str = f"[{item['source'].split('(')[0].strip()}]({item['repository']})" if item['repository'].startswith('http') else item['source']
        wf_samples = ", ".join(item['workflows'][:2])
        if len(item['workflows']) > 2:
            wf_samples += f" (+{len(item['workflows']) - 2})"
        md_content += f"| `{n}` | {repo_str} | {item['stability_rating']} | **{item['used_in_workflows_count']}** | `{wf_samples}` |\n"

    md_content += """
---

## 3. Pre-Update Verification Protocol
1. Take a micro snapshot before executing updates:
   ```bash
   python3 and_os/bin/sys_cli.py snapshot micro -m "Before ComfyUI update"
   ```
2. Run node compatibility verification:
   ```bash
   python3 and_os/bin/comfy_node_registry.py --verify
   ```
3. If missing or renamed nodes are identified, review `comfy_nodes_registry.json`.

---
[[and_os/lib/workflows/comfy/comfy|<- Return to ComfyUI Directory]]
"""
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(md_content)

    # Update proc status file
    os.makedirs(PROC_DIR, exist_ok=True)
    with open(os.path.join(PROC_DIR, "comfy_nodes.stat"), "w", encoding="utf-8") as pf:
        core_cnt = sum(1 for v in registry['nodes'].values() if 'Core' in v['source'])
        custom_cnt = sum(1 for v in registry['nodes'].values() if 'External' in v['source'])
        pf.write(f"COMFY_TOTAL_NODES={len(node_usage)}\n")
        pf.write(f"CORE_NODES={core_cnt}\n")
        pf.write(f"CUSTOM_NODES={custom_cnt}\n")
        pf.write(f"WORKFLOWS_COUNT={len(workflows)}\n")
        pf.write(f"UPDATED={registry['updated_at']}\n")

    return registry

def verify_workflows(target_wf=None):
    """Verify referenced workflow nodes against known database."""
    ext_map = load_extension_map()
    local_custom_pkgs = scan_local_custom_nodes()
    
    workflows_to_check = [target_wf] if target_wf else collect_all_workflows()
    
    print(f"=== ComfyUI Node Integrity Verification ({len(workflows_to_check)} workflows) ===")
    missing_nodes_report = []

    for wf in workflows_to_check:
        nodes = extract_nodes_from_workflow(wf)
        rel_wf = os.path.relpath(wf, VAULT_ROOT) if wf.startswith(VAULT_ROOT) else os.path.basename(wf)
        
        for n in set(nodes):
            is_core = "https://github.com/comfyanonymous/ComfyUI" in ext_map.get(n, [])
            is_local = n.startswith("CHBS_")
            is_known_ext = len(ext_map.get(n, [])) > 0
            
            if not is_core and not is_local and not is_known_ext:
                missing_nodes_report.append((rel_wf, n))

    if not missing_nodes_report:
        print("  [OK] All referenced nodes identified in registry (Core / Custom / CHBS)! Regression risk minimal.")
        return 0
    else:
        print(f"  [WARN] Detected {len(missing_nodes_report)} nodes requiring attention before update:")
        for wf_name, n in missing_nodes_report[:10]:
            print(f"    - {wf_name}: node '{n}' (not found in standard manager map)")
        return len(missing_nodes_report)

def main():
    parser = argparse.ArgumentParser(description="ComfyUI Active Node Registry & Update Guard")
    parser.add_argument("--scan", action="store_true", default=True, help="Scan workflows and build active node database")
    parser.add_argument("--verify", type=str, nargs="?", const="ALL", help="Verify workflow node compatibility")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    args = parser.parse_args()

    if args.verify:
        wf_arg = None if args.verify == "ALL" else args.verify
        verify_workflows(wf_arg)
    else:
        reg = build_registry()
        if args.json:
            print(json.dumps(reg, ensure_ascii=False, indent=2))
        else:
            print("⚡ [ComfyUI Node Registry] Database successfully built and updated!")
            print(f"  • Total distinct node types: {reg['total_distinct_nodes']}")
            print(f"  • Scanned workflows: {reg['total_workflows']}")
            print(f"  • Documentation: and_os/lib/workflows/comfy/comfy_nodes_registry.md")
            print(f"  • JSON manifest: and_os/lib/workflows/comfy/comfy_nodes_registry.json")
            print(f"  • Telemetry: and_os/proc/comfy_nodes.stat")

if __name__ == "__main__":
    main()
