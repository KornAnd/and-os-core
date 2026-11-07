#!/usr/bin/env python3
"""
Task Context Bundler & Output Trimming Utility
AnD os v8.1 - Think in Code Context Squeezer

Collects minimum sufficient context for tasks (signatures, decisions, status)
without reading full multi-megabyte files into LLM memory.
"""

import os
import sys
import json
import glob
import argparse
from pathlib import Path

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../.."))

DOMAINS_MAP = {
    "cg": {
        "manifests": ["and_os/etc/3D_PIPELINE.md", "and_os/lib/skills/cg-pipeline/SKILL.md"],
        "scripts": ["and_os/opt/apps/cg_workspace/cg_core.py"],
        "state_keys": ["3d_pipeline", "pulsar"]
    },
    "dev": {
        "manifests": ["and_os/etc/3D_PIPELINE.md", "Nero/pulsar/cg_tool.md", "and_os/lib/skills/cg-pipeline/SKILL.md"],
        "scripts": ["and_os/opt/apps/cg_workspace/cg_core.py", "and_os/bin/cg_bridge.py"],
        "state_keys": ["3d_pipeline", "pulsar", "cg_workspace"]
    },
    "3d": {
        "manifests": ["and_os/etc/3D_PIPELINE.md", "Nero/pulsar/cg_tool.md"],
        "scripts": ["and_os/opt/apps/cg_workspace/cg_core.py"],
        "state_keys": ["3d_pipeline", "pulsar"]
    },
    "story": {
        "manifests": ["Story/CONTEXT.md", "Book/CONTEXT.md"],
        "scripts": ["and_os/bin/script_chunker.py"],
        "state_keys": ["story"]
    },
    "ftrack": {
        "manifests": ["and_os/lib/skills/ftrack-sync/SKILL.md"],
        "scripts": ["and_os/bin/ftrack_report.py", "and_os/bin/ftrack_sync.py"],
        "state_keys": ["ftrack"]
    },
    "Studio": {
        "manifests": ["Product/Projects/Mars/CONTEXT.md", "and_os/lib/skills/ftrack-sync/SKILL.md"],
        "scripts": ["and_os/bin/ftrack_report.py", "and_os/bin/mattermost_sync.py"],
        "state_keys": ["ftrack", "Studio"]
    },
    "consulting": {
        "manifests": ["CG_core/CONTEXT.md", "Nero/cg_core/CONTEXT.md", "and_os/lib/skills/cg-core-consulting/SKILL.md"],
        "scripts": ["and_os/bin/doc_analyze.py", "and_os/bin/xl_analyze.py"],
        "state_keys": ["cg_core", "consulting"]
    },
    "tabu": {
        "manifests": ["Ta-Bu/CONTEXT.md", "and_os/lib/skills/ta-bu-plan/SKILL.md"],
        "scripts": ["and_os/bin/budget_calc.py", "and_os/bin/app_bridge.py", "and_os/bin/project_registry.py"],
        "state_keys": ["tabu", "pulsar_apps"]
    },
    "know": {
        "manifests": ["Clippings/CONTEXT.md", "Tags/CONTEXT.md"],
        "scripts": ["and_os/bin/audit_tags_links.py", "and_os/bin/clean_links.py"],
        "state_keys": ["quick_knowledge"]
    },
    "system": {
        "manifests": ["SYSTEM.md", "and_os/etc/SYSTEM_MAP.md", "and_os/etc/ISLANDS_ROUTER.md", "and_os/etc/SYSTEM_GRAPH_REGISTRY.json"],
        "scripts": ["and_os/bin/sys_cli.py", "and_os/bin/validate_system.py"],
        "state_keys": ["system"]
    },
    "terminal": {
        "manifests": ["Terminal/CONTEXT.md", "Nero/pulsar/and_terminal.md"],
        "scripts": ["and_os/bin/sys_bus.py", "and_os/bin/kernel_daemon.py"],
        "state_keys": ["terminal", "events", "kernel"]
    }
}

def extract_signatures_from_py(file_path: str, max_lines: int = 40) -> list:
    """Extracts top docstring and def/class lines from python file."""
    if not os.path.exists(file_path):
        return []
    signatures = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if line.startswith("def ") or line.startswith("class ") or line.startswith("@"):
                    signatures.append(f"L{idx+1}: {line.strip()}")
                elif idx < 15 and line.strip().startswith('"""'):
                    signatures.append(line.strip())
    except (OSError, UnicodeDecodeError) as e:
        sys.stderr.write(f"[context_bundler] Warning reading signatures {py_file}: {e}\n")
    return signatures[:max_lines]

def bundle_domain_context(domain: str) -> dict:
    """Builds a condensed, token-efficient bundle for the target domain."""
    dinfo = DOMAINS_MAP.get(domain.lower())
    if not dinfo:
        return {"error": f"Unknown domain: {domain}. Available: {list(DOMAINS_MAP.keys())}"}
        
    bundle = {
        "domain": domain,
        "manifests_summary": {},
        "code_signatures": {},
        "state_snapshot": {}
    }
    
    # 1. Manifest Headers
    for m in dinfo.get("manifests", []):
        mpath = os.path.join(VAULT_ROOT, m)
        if os.path.exists(mpath):
            try:
                with open(mpath, "r", encoding="utf-8") as f:
                    lines = [f.readline() for _ in range(25)]
                    bundle["manifests_summary"][m] = "".join(lines).strip()
            except (OSError, UnicodeDecodeError) as e:
                sys.stderr.write(f"[context_bundler] Warning reading manifest {mpath}: {e}\n")
                
    # 2. Code Signatures
    for s in dinfo.get("scripts", []):
        spath = os.path.join(VAULT_ROOT, s)
        bundle["code_signatures"][s] = extract_signatures_from_py(spath)
        
    # 3. State DB Cache
    state_file = os.path.join(VAULT_ROOT, "Nero/ai/cache/domain_states.json")
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                sdata = json.load(f)
                for k in dinfo.get("state_keys", []):
                    if k in sdata:
                        bundle["state_snapshot"][k] = sdata[k]
        except (OSError, json.JSONDecodeError) as e:
            sys.stderr.write(f"[context_bundler] Warning loading state: {e}\n")
            
    return bundle

def format_bundle_markdown(bundle: dict) -> str:
    """Formats bundled context into an ultra-clean, dense markdown string."""
    if "error" in bundle:
        return f"❌ {bundle['error']}"
        
    md = []
    md.append(f"### ⚡ CONTEXT BUNDLE: [{bundle['domain'].upper()}]")
    md.append(f"---")
    
    md.append(f"#### 1. Manifest Excerpts")
    for m, text in bundle["manifests_summary"].items():
        md.append(f"**`{m}`:**\n```markdown\n{text[:400]}...\n```")
        
    md.append(f"#### 2. Key Code Signatures")
    for s, sigs in bundle["code_signatures"].items():
        md.append(f"**`{s}`:**")
        md.append("```python\n" + "\n".join(sigs[:15]) + "\n```")
        
    if bundle["state_snapshot"]:
        md.append(f"#### 3. State Snapshot")
        md.append("```json\n" + json.dumps(bundle["state_snapshot"], indent=2, ensure_ascii=False) + "\n```")
        
    return "\n".join(md)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Task Context Bundler")
    parser.add_argument("domain", choices=list(DOMAINS_MAP.keys()), help="Target domain")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()
    
    b = bundle_domain_context(args.domain)
    if args.json:
        print(json.dumps(b, indent=2, ensure_ascii=False))
    else:
        print(format_bundle_markdown(b))
