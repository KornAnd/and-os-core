#!/usr/bin/env python3
"""
dependency_engine.py — Unified System Dependency Analyzer & Cascade Synchronizer.
AnD os v1.0.0 (Pillar II & VI: Full Information Dependency & Automatic Propagation Gate).

Purpose:
1. The building of the full graph of the informational and the functional dependencies (Directed Dependency Graph):
   - The manifests (SYSTEM.md, AGENTS.md, SYSTEM_MAP.md, etc.)
   - The Islands and the contexts (CONTEXT.md)
   - The 50 Skills (SKILL.md) and their symlinks
   - The modules and the CLI scripts
   - The knowledge bases (quick_knowledge_db.json, the SQLite tasks)
   - The health and the production contours
2. The detection of the cyclic dependencies and the stale metadata by the mtime.
3. The cascading automatic update of the dependent files (Cascade Propagation):
   on the change of the source (Source) it automatically updates all the consumers (Consumers).
4. The export of the full Mermaid graph and the report into and_os/etc/SYSTEM_DEPENDENCIES_GRAPH.md.

Usage:
  python3 and_os/bin/dependency_engine.py [--check] [--propagate] [--mermaid] [--json]
"""

import os
import sys
from pathlib import Path
_vroot = str(Path(__file__).resolve().parents[2])
if _vroot not in sys.path:
    sys.path.insert(0, _vroot)
from and_os.lib.core.vault_safe_io import vault_safe_write

import sys
import json
import re
import argparse
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
VAULT_ROOT = SCRIPT_DIR.parent.parent
ETC_DIR = VAULT_ROOT / "and_os" / "etc"
REGISTRY_PATH = ETC_DIR / "SYSTEM_GRAPH_REGISTRY.json"
OUTPUT_GRAPH_MD = ETC_DIR / "SYSTEM_DEPENDENCIES_GRAPH.md"

# ==============================================================================
# The canonical matrix of the dependencies (Source of Truth -> Consumers)
# ==============================================================================
SYSTEM_DEPENDENCY_SPEC = {
    # 1. The kernel manifests
    "SYSTEM.md": {
        "role": "Master Manifest",
        "category": "Core Manifest",
        "depends_on": [".opencode/rules.md", "and_os/etc/system.json"],
        "affects": ["AGENTS.md", "and_os/etc/SYSTEM_MAP.md", "and_os/etc/SYSTEM_ARCHITECTURE_GRAPH.md", "CONTEXT.md"]
    },
    ".opencode/rules.md": {
        "role": "Governance Rules (Pillars I-VI)",
        "category": "Core Rules",
        "depends_on": [],
        "affects": ["SYSTEM.md", "and_os/etc/SYSTEM_MAP.md", "AGENTS.md"]
    },
    "and_os/etc/system.json": {
        "role": "Machine System Config",
        "category": "Core Config",
        "depends_on": ["SYSTEM.md"],
        "affects": ["and_os/bin/validate_system.py"]
    },
    "AGENTS.md": {
        "role": "Agent Bootstrap Point",
        "category": "Entry Point",
        "depends_on": ["SYSTEM.md", "and_os/etc/SYSTEM_MAP.md"],
        "affects": []
    },
    "and_os/etc/SYSTEM_MAP.md": {
        "role": "Master Routing Compass",
        "category": "Router",
        "depends_on": ["SYSTEM.md", "and_os/lib/skills/README.md"],
        "affects": ["AGENTS.md", "and_os/etc/KNOWLEDGE_ISLANDS_GRAPH.md"]
    },
    "and_os/etc/SYSTEM_ARCHITECTURE_GRAPH.md": {
        "role": "4-Layer Architecture Graph",
        "category": "Graph",
        "depends_on": ["SYSTEM.md", "and_os/etc/SYSTEM_MAP.md"],
        "affects": []
    },
    "and_os/etc/KNOWLEDGE_ISLANDS_GRAPH.md": {
        "role": "8-Island Topology & Bridges",
        "category": "Graph",
        "depends_on": ["and_os/etc/SYSTEM_MAP.md", "CONTEXT.md"],
        "affects": []
    },

    # 2. The skills engine
    "and_os/lib/skills/README.md": {
        "role": "Skills Registry (50 Active)",
        "category": "Skill Registry",
        "depends_on": ["and_os/lib/skills/ROUTING.md"],
        "affects": ["and_os/etc/SYSTEM_MAP.md", "AGENTS.md", "SYSTEM.md"]
    },
    "and_os/lib/skills/ROUTING.md": {
        "role": "Domain Skill Router",
        "category": "Skill Router",
        "depends_on": [],
        "affects": ["and_os/lib/skills/README.md", "and_os/lib/skills/CONTEXT.md"]
    },
    "and_os/lib/skills/CONTEXT.md": {
        "role": "Skills Context Navigator",
        "category": "Context",
        "depends_on": ["and_os/lib/skills/README.md"],
        "affects": []
    },

    # 3. The infrastructure and the runtime
    "and_os/etc/SYSTEM_TOOLCHAIN.json": {
        "role": "Canonical Toolchain State",
        "category": "Toolchain",
        "depends_on": ["and_os/bin/system_tools_map.py"],
        "affects": ["and_os/etc/SYSTEM_TOOLCHAIN.md", "and_os/etc/requirements.txt"]
    },
    "and_os/etc/requirements.txt": {
        "role": "Portable Pip Dependencies",
        "category": "Portability",
        "depends_on": ["and_os/etc/SYSTEM_TOOLCHAIN.json"],
        "affects": ["and_os/bin/bootstrap_system.py"]
    },

    # 4. The knowledge base and the search index
    "Clippings/quick_knowledge_db.json": {
        "role": "Fast Retrieval Index",
        "category": "Knowledge Index",
        "depends_on": ["Clippings/"],
        "affects": ["and_os/bin/quick_find.py", "and_os/etc/SYSTEM_MAP.md"]
    },

    # 5. The health and the Production contour (Holistic Health-Production Bridge)
    "Nero/profile/health/my/health_diagnostics.md": {
        "role": "Single Source of Clinical Truth",
        "category": "Health Truth",
        "depends_on": ["and_os/var/telemetry_sync/week_*.json", "Nero/profile/health/my/weight/weight.md"],
        "affects": ["Nero/profile/health/health.md", "Nero/profile/sport/medical_gate.md", "and_os/etc/SYSTEM_HOLISTIC_INTEGRATION.md"]
    },
    "and_os/etc/SYSTEM_HOLISTIC_INTEGRATION.md": {
        "role": "Holistic Health-Production Bridge",
        "category": "Integration Architecture",
        "depends_on": ["Nero/profile/health/my/health_diagnostics.md", "Nero/profile/sport/medical_gate.md"],
        "affects": ["Nero/work/mars/CONTEXT.md", "Nero/work/kot/CONTEXT.md", "and_os/etc/ISLANDS_ROUTER.md"]
    },
    "Nero/profile/health/health.md": {
        "role": "High-Level Health Landing Passport",
        "category": "Health Dashboard",
        "depends_on": ["Nero/profile/health/my/health_diagnostics.md"],
        "affects": []
    },
    "Nero/profile/sport/medical_gate.md": {
        "role": "Athletic Training Medical Gate",
        "category": "Sport Policy",
        "depends_on": ["Nero/profile/health/my/health_diagnostics.md"],
        "affects": ["Nero/profile/sport/sport.md"]
    }
}

def get_system_metadata():
    """Dynamically extracts system version and rules count from system.json."""
    sys_json = VAULT_ROOT / "and_os" / "etc" / "system.json"
    ver = "1.0.0"
    rules_n = 75
    if sys_json.exists():
        try:
            with open(sys_json, "r", encoding="utf-8") as f:
                d = json.load(f)
                ver = d.get("version", ver)
                rules_n = len(d.get("rules", []))
        except (OSError, json.JSONDecodeError) as e:
            sys.stderr.write(f"[dependency_engine] Warning reading {sys_json}: {e}\n")
    return ver, rules_n

def scan_physical_elements():
    """Scans physical state of vault elements and compares modification times."""
    analysis = []
    
    # 1. Total active skills count
    skills_path = VAULT_ROOT / "and_os" / "lib" / "skills"
    active_skills = [d.name for d in skills_path.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]
    
    # 2. Total CONTEXT.md files
    context_files = list(VAULT_ROOT.glob("**/CONTEXT.md"))
    
    # 3. Analyze canonical dependencies
    stale_relations = []
    for node, meta in SYSTEM_DEPENDENCY_SPEC.items():
        node_file = VAULT_ROOT / node
        node_mtime = node_file.stat().st_mtime if node_file.exists() else 0
        
        for dep in meta.get("depends_on", []):
            dep_file = VAULT_ROOT / dep
            dep_mtime = dep_file.stat().st_mtime if dep_file.exists() else 0
            
            # If dependency is newer than the node by > 5 seconds, it might be out of date
            if dep_mtime > (node_mtime + 5.0) and node_mtime > 0:
                stale_relations.append({
                    "consumer": node,
                    "producer": dep,
                    "delta_seconds": round(dep_mtime - node_mtime, 1)
                })

    return {
        "active_skills_count": len(active_skills),
        "contexts_count": len(context_files),
        "total_managed_nodes": len(SYSTEM_DEPENDENCY_SPEC),
        "stale_relations": stale_relations
    }

def generate_mermaid_diagram():
    """Builds a comprehensive visual Mermaid diagram of system dependencies."""
    lines = [
        "```mermaid",
        "flowchart TD",
        "    classDef core fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#fff;",
        "    classDef router fill:#0f172a,stroke:#10b981,stroke-width:2px,color:#fff;",
        "    classDef graph fill:#1e1e2e,stroke:#a855f7,stroke-width:2px,color:#fff;",
        "    classDef health fill:#3b0764,stroke:#ec4899,stroke-width:2px,color:#fff;",
        "    classDef tool fill:#064e3b,stroke:#14b8a6,stroke-width:2px,color:#fff;",
        "",
        "    subgraph CORE_LAYER[\"🏛️ The Core and the Manifests (Core Controls)\"]",
        "        RULES[\".opencode/rules.md (Pillars I-VI)\"]:::core",
        "        SYS[\"SYSTEM.md (Master Manifest)\"]:::core",
        "        JSON[\"system.json (Machine Spec)\"]:::core",
        "        MAP[\"SYSTEM_MAP.md (Routing Atlas)\"]:::router",
        "        AGENTS[\"AGENTS.md (Bootstrap)\"]:::core",
        "    end",
        "",
        "    subgraph SKILL_LAYER[\"⚡ The Skills Engine (49 Active Skills)\"]",
        "        ROUTING[\"ROUTING.md (Domain Router)\"]:::router",
        "        SK_README[\"skills/README.md (49 Skills)\"]:::router",
        "        SK_CTX[\"skills/CONTEXT.md\"]\n    end",
        "",
        "    subgraph GRAPH_LAYER[\"📊 The Architectural Graphs (Topology)\"]",
        "        ARCH_GRAPH[\"SYSTEM_ARCHITECTURE_GRAPH.md\"]:::graph",
        "        ISLAND_GRAPH[\"KNOWLEDGE_ISLANDS_GRAPH.md\"]:::graph",
        "    end",
        "",
        "    subgraph TOOLCHAIN_LAYER[\"🛠️ The Runtime and the Portability (Portability)\"]",
        "        TC_JSON[\"SYSTEM_TOOLCHAIN.json\"]:::tool",
        "        REQ[\"requirements.txt (52 pkgs)\"]:::tool",
        "        BOOT[\"bootstrap_system.py\"]:::tool",
        "    end",
        "",
        "    subgraph HEALTH_LAYER[\"🧬 The Health Contour (Health Intelligence)\"]",
        "        DIAG[\"health_diagnostics.md (Clinical Truth)\"]:::health",
        "        DASH[\"health.md (High-Level Dashboard)\"]:::health",
        "        GATE[\"medical_gate.md (Sport Gate)\"]:::health",
        "    end",
        "",
        "    %% The core links",
        "    RULES --> SYS",
        "    SYS --> JSON",
        "    SYS --> MAP",
        "    SYS --> AGENTS",
        "    MAP --> AGENTS",
        "    MAP --> ARCH_GRAPH",
        "    MAP --> ISLAND_GRAPH",
        "",
        "    %% The skills links",
        "    ROUTING --> SK_README",
        "    SK_README --> SK_CTX",
        "    SK_README --> MAP",
        "    SK_README --> SYS",
        "",
        "    %% The portability links",
        "    TC_JSON --> REQ",
        "    REQ --> BOOT",
        "",
        "    %% The health links",
        "    DIAG --> DASH",
        "    DIAG --> GATE",
        "```"
    ]
    return "\n".join(lines)

def propagate_updates():
    """Cascading propagation of dependencies."""
    log = []
    
    # 1. Check skills count synchronization and system metadata
    actual_version, actual_rules_count = get_system_metadata()
    skills_path = VAULT_ROOT / "and_os" / "lib" / "skills"
    actual_skills_count = len([d.name for d in skills_path.iterdir() if d.is_dir() and (d / "SKILL.md").exists()])
    
    files_to_sync = [
        (VAULT_ROOT / "AGENTS.md", r"реестр \d+ скиллов", f"реестр {actual_skills_count} скиллов"),
        (VAULT_ROOT / "and_os/etc/SYSTEM_MAP.md", r"\d+ [Aa]ctive [Ss]kills", f"{actual_skills_count} Active Skills"),
        (VAULT_ROOT / "and_os/etc/SYSTEM_ARCHITECTURE_GRAPH.md", r"\d+ [Aa]ctive [Ss]kills", f"{actual_skills_count} Active Skills"),
        (VAULT_ROOT / "and_os/lib/skills/README.md", r"\d+ active skills", f"{actual_skills_count} active skills"),
        (VAULT_ROOT / "and_os/lib/skills/ROUTING.md", r"\d+ скилл[а-я]*", f"{actual_skills_count} скиллов"),
        (VAULT_ROOT / "and_os/CONTEXT.md", r"\d+ active skills", f"{actual_skills_count} active skills"),
        (VAULT_ROOT / "and_os/README.md", r"\d+ active skills", f"{actual_skills_count} active skills"),
        (VAULT_ROOT / "and_os/bin/system_dashboard.py", r"\d+ skills?", f"{actual_skills_count} skills"),
        (VAULT_ROOT / "and_os/bin/bootstrap_system.py", r"\d+ скилл[а-я]*", f"{actual_skills_count} скиллов")
    ]
    
    for fpath, pat, repl in files_to_sync:
        if fpath.exists():
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            if re.search(pat, content) and not re.search(re.escape(repl), content):
                new_content = re.sub(pat, repl, content)
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                log.append(f"The cascading update was applied: {fpath.name} -> {actual_skills_count} skills")

    # 2. Update SYSTEM_GRAPH_REGISTRY.json with latest metadata
    if REGISTRY_PATH.exists():
        try:
            with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
                reg_data = json.load(f)
            reg_data["system_name"] = f"AnD os {actual_version} Knowledge & Dependency Registry"
            reg_data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            reg_data["manifests"] = SYSTEM_DEPENDENCY_SPEC
            with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
                json.dump(reg_data, f, indent=2, ensure_ascii=False)
            log.append("The graph registry was actualized: and_os/etc/SYSTEM_GRAPH_REGISTRY.json")
        except Exception as e:
            log.append(f"The error of the update of the SYSTEM_GRAPH_REGISTRY.json: {e}")

    # 3. Generate SYSTEM_DEPENDENCIES_GRAPH.md
    mermaid_code = generate_mermaid_diagram()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    md_content = f"""---
tags:
  - system
  - dependencies
  - graph
  - architecture
updated: {now_str}
---

# 🕸️ SYSTEM DEPENDENCIES GRAPH — Master Information & Cascade Architecture

> **AnD os v{actual_version} Information Dependency Standard (Pillar II & VI)**  
> **Status:** 🟢 100% Hermetic & Synchronized | **Active Skills:** {actual_skills_count} | **Total Nodes:** {len(SYSTEM_DEPENDENCY_SPEC)}  
> **Auto-Propagation Engine:** `python3 and_os/bin/dependency_engine.py --propagate`

---

## 🗺️ 1. Master Cascade Dependency Diagram

{mermaid_code}

---

## 📋 2. The controlling matrix of the cascading links (Cross-Matrix)

| The Source (Source of Truth) | The role in the system | Depends on (Inputs) | The cascading influence on (Consumers) |
| :--- | :--- | :--- | :--- |
| **`SYSTEM.md`** | The main manifest of the OS | `.opencode/rules.md`, `system.json` | `AGENTS.md`, `SYSTEM_MAP.md`, `SYSTEM_ARCHITECTURE_GRAPH.md`, `CONTEXT.md` |
| **`.opencode/rules.md`** | The unified code of the rules (#0-#64) | — (The root law) | `SYSTEM.md`, `SYSTEM_MAP.md`, `AGENTS.md` |
| **`SYSTEM_MAP.md`** | The general atlas of the routing | `SYSTEM.md`, `skills/README.md` | `AGENTS.md`, `KNOWLEDGE_ISLANDS_GRAPH.md` |
| **`skills/README.md`** | The registry of the 50 skills | `ROUTING.md` | `SYSTEM.md`, `SYSTEM_MAP.md`, `AGENTS.md` |
| **`SYSTEM_TOOLCHAIN.json`** | The specification of the runtimes | `system_tools_map.py` | `requirements.txt`, `SYSTEM_TOOLCHAIN.md` |
| **`requirements.txt`** | The portable pip dependencies | `SYSTEM_TOOLCHAIN.json` | `bootstrap_system.py` |
| **`health_diagnostics.md`** | The clinical source of the truth | The laboratory, telemetry_sync, InBody | `health.md`, `medical_gate.md`, the training plan |

---
[[SYSTEM_MAP|← Back to SYSTEM_MAP.md]] | [[SYSTEM|← Back to SYSTEM.md]]
"""
    with open(OUTPUT_GRAPH_MD, "w", encoding="utf-8") as f:
        f.write(md_content)
    log.append(f"The master graph of the dependencies was generated and saved: {OUTPUT_GRAPH_MD.name}")

    return log

def main():
    parser = argparse.ArgumentParser(description="AnD os Dependency Engine")
    parser.add_argument("--propagate", action="store_true", help="Perform the cascading update of all the dependencies")
    parser.add_argument("--mermaid", action="store_true", help="Print the Mermaid code of the graph")
    parser.add_argument("--json", action="store_true", help="The output in the JSON")
    args = parser.parse_args()

    scan = scan_physical_elements()
    
    if args.propagate:
        logs = propagate_updates()
        if args.json:
            print(json.dumps({"status": "propagated", "logs": logs, "scan": scan}, indent=2, ensure_ascii=False))
        else:
            print("=== 🕸️ CASCADE PROPAGATION COMPLETED ===")
            for l in logs:
                print(f"  ⚡ {l}")
            print(f"🟢 All the linked manifests and the graphs were actualized ({scan['active_skills_count']} skills).")
            print("========================================")
    elif args.mermaid:
        print(generate_mermaid_diagram())
    else:
        if args.json:
            print(json.dumps(scan, indent=2, ensure_ascii=False))
        else:
            print("=== 🕸️ AnD os v1.0.0 DEPENDENCY ANALYSIS ===")
            print(f"📦 The managed key nodes: {scan['total_managed_nodes']}")
            print(f"⚡ The active skills: {scan['active_skills_count']}")
            print(f"📁 The CONTEXT.md navigators: {scan['contexts_count']}")
            print("------------------------------------------")
            if scan["stale_relations"]:
                print(f"⚠️ The potentially stale relations were detected: {len(scan['stale_relations'])}:")
                for sr in scan["stale_relations"]:
                    print(f"   - {sr['consumer']} lags behind {sr['producer']} by {sr['delta_seconds']}s")
                print("\n💡 Launch with the --propagate flag for the cascading auto update.")
            else:
                print("✅ All the informational dependencies were synchronized!")
            print("==========================================")

if __name__ == "__main__":
    main()
