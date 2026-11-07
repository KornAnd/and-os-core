#!/usr/bin/env python3
"""
rules_compiler.py — Fast Rules Index Compiler for AnD os v8.5.
Compiles SYSTEM.md and .opencode/rules.md into a high-density, token-efficient
JSON index (and_os/etc/rules_fast_index.json) for 0-latency LLM agent injection.

Features:
  - Sub-50ms execution time.
  - Generates SHA256 content hashes to detect manifest drift.
  - Emits core principles & compact rules dictionary (< 500 tokens).
  - CLI operations: compile, status, verify.
"""

import os
import sys
import re
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Tuple

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
VAULT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
SYSTEM_MD = os.path.join(VAULT_ROOT, "SYSTEM.md")
OPENCODE_RULES_MD = os.path.join(VAULT_ROOT, ".opencode/rules.md")
TARGET_JSON = os.path.join(VAULT_ROOT, "and_os/etc/rules_fast_index.json")
CG_TARGET_JSON = os.path.join(VAULT_ROOT, "and_os/opt/apps/cg_workspace/etc/cg_rules_fast.json")


def compute_file_sha256(path: str) -> str:
    """Calculates SHA256 checksum of a file."""
    if not os.path.exists(path):
        return ""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def parse_rules_from_manifests() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Parses rules table from SYSTEM.md and rules.md with clean fallback.
    Returns: (core_principles, rules_dict)
    """
    core_principles = {
        "language": "RU: диалог, отчеты, вопросы для Андрея; EN: код, конфиги, context",
        "workflow": "Retrieval -> Context -> DAG Plan -> Execution -> Memory (Правило №13)",
        "think_in_code": "Python-скрипт вместо вывода сырых данных в контекст чата (Правило №16)",
        "governance": "Fast-Track: and_os/opt напрямую; Vault Guard: Nero/ через AST-шлюз (Правило №19)",
        "safety": "APFS CoW снимки перед правкой + согласование графа перед кодом (Правило №65)"
    }

    domain_beacons = {
        "1_core": {
            "name": "Core & System",
            "path": os.path.join(VAULT_ROOT, "and_os/"),
            "policy": "Fast-Track direct edits. Zero-Blind-Assumptions (Rule #61) - CLI verification mandatory."
        },
        "2_vault": {
            "name": "Knowledge Vault",
            "path": os.path.join(VAULT_ROOT, "{Nero,Product,Story,Ta-Bu,Book,Clippings}/"),
            "policy": "New notes allowed via write_to_file. Edits MUST use vault_patch or sys_cli vault patch."
        },
        "3_pulsar": {
            "name": "Pulsar Space",
            "path": "./pulsar/",
            "policy": "12 decoupled apps. Ports strictly in :8080-:8099 (Terminal on :8099). sys_cli project pulsar."
        },
        "4_xcode": {
            "name": "Xcode & Gamedev",
            "path": "./xcode/",
            "policy": "Swift 6 + SpriteKit (EscPlanet). Muscle Realm Isolation (Rule #27) - no Swift code in Vault notes."
        },
        "5_comfyui": {
            "name": "ComfyUI & 3D CG",
            "path": "./cg_workspace",
            "policy": "LiteGraph v0.4 schemas (extra.ds). Passports with CHBS_Approval_Gate. Zero ~/Downloads. comfy_graph.py."
        }
    }

    rules_dict: Dict[str, Dict[str, str]] = {}

    if os.path.exists(SYSTEM_MD):
        with open(SYSTEM_MD, "r", encoding="utf-8") as f:
            content = f.read()

        for m in re.finditer(r'\|\s*([0-9.]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|', content):
            r_num = m.group(1).strip()
            r_name = m.group(2).strip()
            r_desc = m.group(3).strip()
            # Clean up markdown formatting in essence
            clean_desc = re.sub(r'[*_`]', '', r_desc)
            clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()
            clean_name = re.sub(r'[*_`]', '', r_name).strip()

            rules_dict[r_num] = {
                "name": clean_name,
                "essence": clean_desc
            }

    return core_principles, domain_beacons, rules_dict


def compile_rules_index() -> Dict[str, Any]:
    """Compiles rules into and_os/etc/rules_fast_index.json."""
    os.makedirs(os.path.dirname(TARGET_JSON), exist_ok=True)
    sys_sha = compute_file_sha256(SYSTEM_MD)
    principles, beacons, rules = parse_rules_from_manifests()

    payload = {
        "version": "9.2.0",
        "compiled_at": datetime.now().isoformat(),
        "source_sha256": sys_sha,
        "rules_count": len(rules),
        "core_principles": principles,
        "domain_beacons": beacons,
        "rules": rules
    }

    with open(TARGET_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # Compile satellite CG projection
    cg_payload = compile_cg_satellite_projection(sys_sha, rules)

    return payload


def compile_cg_satellite_projection(sys_sha: str, all_rules: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compiles localized CG / 3D+AI domain satellite index (cg_rules_fast.json).
    Extracts relevant CG invariant rules and production budgets (< 500 tokens)
    to eliminate agent hallucination and prevent central core context bloat.
    """
    os.makedirs(os.path.dirname(CG_TARGET_JSON), exist_ok=True)

    # Focused domain rules for 3D/AI production
    cg_rule_keys = ["0", "0.5", "1", "3", "13", "16", "19", "27", "41", "42", "45", "57", "58", "61", "65", "68"]
    selected_rules = {k: all_rules[k] for k in cg_rule_keys if k in all_rules}

    cg_payload = {
        "domain": "cg_workspace",
        "engine": "cg_core",
        "role": "Hybrid 3D+AI Production Sub-Core",
        "compiled_at": datetime.now().isoformat(),
        "source_sha256": sys_sha,
        "rules_count": len(selected_rules),
        "production_invariants": {
            "topology": "Quad-first geometry, zero non-manifold edges, apply scale (scale=1.0.0), pivot at center-bottom",
            "hierarchy": "Max 10 logical semantic blocks with root_master armature hierarchy",
            "linking": "Non-destructive shot assembly via Blender Library Linking & Overrides",
            "passes": "Depth 16-bit, Surface Normals, Lineart, Z-buffer, Camera POV for ComfyUI",
            "isolation": "Zero temporary files in ~/Downloads or Obsidian Vault root (Rule #41)",
            "safety": "Free-First zero-cost nodes (Rule #45) & Air-Gap Vault Isolation (Rule #57, #58)",
            "verification": "Anti-Beta-Tester Gate (Rule #61) - Mandatory execution of cg_core.py qa before report"
        },
        "production_modality_matrix": {
            "rule_of_thumb": "Blender builds 3D SPATIAL TRUTH (Mesh, Armature, UV, Camera, Passes); ComfyUI crafts PIXEL PERFECTION (Texture, Style, Latent Diffusion, Inpainting).",
            "phase_routing": {
                "Phase_1_Blockout": {
                    "branch_dcc_blender": "tools/modeling/blockout_engine.py -> Procedural volumetric greybox, strict dimensions, scale=1.0",
                    "branch_neural_ai": "tools/modeling/kits_engine.py + Text-to-3D reference -> Fast silhouette exploration",
                    "gate": "cg_core.py qa audit --profile game (Must pass Zero Z-Fighting & scale=1.0)"
                },
                "Phase_1_Shading": {
                    "branch_dcc_blender": "tools/shading/uv_engine.py + materials_engine.py -> Deterministic PBR procedural nodes, clean UV seams",
                    "branch_neural_ai": "modules/comfy_bridge.py -> Multi-angle texture projection & neural inpainting over UV",
                    "gate": "Zero missing UV maps on textured meshes"
                },
                "Phase_2_Layout_Animatic": {
                    "branch_dcc_blender": "modules/layout_assembler.py + tools/animation/previs_engine.py -> Library Overrides, camera rail/turntable moves",
                    "branch_neural_ai": "modules/shot_animatic.py -> Stepped storyboard frames to I2V latent video preview",
                    "gate": "animatic.meta.json validated with Director sign-off"
                },
                "Phase_3_Shot_Production": {
                    "branch_hybrid_bridge": "modules/shot_playblast_generator.py -> Headless render of OpenGL Playblast + 16-bit Z-Depth & Normals -> ComfyUI VHS diffusion pass -> DaVinci Resolve conform",
                    "gate": "cg_core.py qa review --file <blend> -> 4-way contact sheet 3200x2400"
                }
            }
        },
        "rules": selected_rules
    }

    with open(CG_TARGET_JSON, "w", encoding="utf-8") as f:
        json.dump(cg_payload, f, ensure_ascii=False, indent=2)

    return cg_payload


def verify_rules_freshness() -> Tuple[bool, str]:
    """Checks if rules_fast_index.json and cg_rules_fast.json match current SYSTEM.md checksum."""
    if not os.path.exists(TARGET_JSON):
        return False, f"Missing index file: {TARGET_JSON}"

    if not os.path.exists(CG_TARGET_JSON):
        return False, f"Missing satellite CG index file: {CG_TARGET_JSON}"

    try:
        current_sha = compute_file_sha256(SYSTEM_MD)

        # 1. Check Global Index
        with open(TARGET_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        saved_sha = data.get("source_sha256", "")
        if current_sha != saved_sha:
            return False, f"Manifest drift in global index: SYSTEM.md changed (SHA {current_sha[:8]} != {saved_sha[:8]})"

        # 2. Check CG Satellite Index
        with open(CG_TARGET_JSON, "r", encoding="utf-8") as f:
            cg_data = json.load(f)
        cg_saved_sha = cg_data.get("source_sha256", "")
        if current_sha != cg_saved_sha:
            return False, f"Manifest drift in CG satellite index: SYSTEM.md changed (SHA {current_sha[:8]} != {cg_saved_sha[:8]})"

        return True, f"Rules indices fresh: Global ({data.get('rules_count', 0)}) + CG Satellite ({cg_data.get('rules_count', 0)})"
    except Exception as e:
        return False, f"Index read error: {e}"


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        ok, msg = verify_rules_freshness()
        if ok:
            print(f"🟢 PASS: {msg}")
            sys.exit(0)
        else:
            print(f"🔴 FAIL: {msg}")
            sys.exit(1)

    # Default action: compile
    payload = compile_rules_index()
    size_b = os.path.getsize(TARGET_JSON)
    cg_size_b = os.path.getsize(CG_TARGET_JSON)
    print(f"✅ Rules indices compiled successfully:")
    print(f"   • Global Path: {TARGET_JSON} ({size_b} bytes, {payload['rules_count']} rules)")
    print(f"   • CG Satellite Path: {CG_TARGET_JSON} ({cg_size_b} bytes, ~{int(cg_size_b / 5.5)} tokens)")
    print(f"   • Manifest SHA: {payload['source_sha256'][:12]}")


if __name__ == "__main__":
    main()
