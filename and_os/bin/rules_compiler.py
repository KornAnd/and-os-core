#!/usr/bin/env python3
"""
rules_compiler.py — Fast Rules Index Compiler for AnD os (v2, audit R2 P3).

Compiles the canonical manifest (and_os/etc/system.json — SSoT) into a
compact, token-efficient JSON index (and_os/etc/rules_fast_index.json)
for 0-latency LLM session-start injection (OpenCode `instructions`).

v2 design (token economy, finding C1):
  - rules: one ultra-compact title per canonical rule = one-liner prefix before ':'
    (rule count is SSoT: and_os/etc/system.json; never hardcode it here)
    (the full per-rule text stays lazy in .opencode/rules.md)
  - source_sha256: sha256 over SYSTEM.md || rules.md || etc/system.json
    (three-source drift detection, no single-file blind spot)
  - size self-policing: the compile REFUSES to write when the serialized
    index exceeds the 6 KB session-start budget (budget is a contract,
    not a hope — the same check re-runs in verify)
  - consumer contract preserved: version, rules_count, core_principles,
    domain_beacons (session_gate.py / vault_guard_hook.py read these keys)
  - domain beacons use portable paths (no absolute home paths)
  - CG satellite (cg_rules_fast.json) keeps its {name, essence} shape for
    the CG app reader; it is not session-injected and has no size budget

Features:
  - Sub-50ms execution time.
  - CLI operations: compile (default), status, verify.

Consumers (do not break):
  - and_os/lib/core/release_ledger.py  -> compile_rules_index()
  - and_os/bin/quick_verify.py Phase 8 -> verify_rules_freshness() / compile_rules_index()
  - and_os/bin/session_gate.py         -> version, rules_count, core_principles, domain_beacons
  - and_os/bin/vault_guard_hook.py     -> domain_beacons
"""

import os
import re
import sys
sys.dont_write_bytecode = True  # Rule #71: no bytecode leaks from entrypoints.
import json
import time
import hashlib
from typing import Any, Dict, Tuple

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
VAULT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
SYSTEM_MD = os.path.join(VAULT_ROOT, "SYSTEM.md")
OPENCODE_RULES_MD = os.path.join(VAULT_ROOT, ".opencode/rules.md")
CANONICAL_SYSTEM_JSON = os.path.join(VAULT_ROOT, "and_os", "etc", "system.json")
TARGET_JSON = os.path.join(VAULT_ROOT, "and_os", "etc", "rules_fast_index.json")
CG_TARGET_JSON = os.path.join(VAULT_ROOT, "and_os", "opt", "apps", "cg_workspace", "etc", "cg_rules_fast.json")

# Session-start injection budget (finding C1, approved 11.11): the index is
# injected into every session, so its byte size is a hard contract.
SIZE_BUDGET_BYTES = 6 * 1024

# CG satellite budget (C13 F3): the sub-core capsule contract is a ~500-token
# fast index loaded on every CG task. 3 KB ~= 750 tokens max with headroom;
# the pre-C13 payload was 9.7 KB (~1700 tokens) — a 5.5x budget violation.
CG_SATELLITE_BUDGET_BYTES = 3 * 1024

# Three source files defining the index: any change to any of them must
# invalidate the compiled sha256 (drift detection).
SHA_SOURCES = (SYSTEM_MD, OPENCODE_RULES_MD, CANONICAL_SYSTEM_JSON)


def compute_file_sha256(path: str) -> str:
    """Calculates SHA256 checksum of a file."""
    if not os.path.exists(path):
        return ""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def compute_combined_sha256() -> str:
    """sha256 over the concatenated bytes of all SHA_SOURCES (v2 drift guard)."""
    h = hashlib.sha256()
    for path in SHA_SOURCES:
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
    return h.hexdigest()


def rule_title(one_liner: str) -> str:
    """Ultra-compact rule title: the one-liner prefix before the first ':'."""
    return one_liner.split(":", 1)[0].strip() if ":" in one_liner else one_liner.strip()

def build_core_principles() -> Dict[str, str]:
    """Minimal operating principles (consumer: session_gate.py)."""
    return {
        "language": "RU: dialogue/reports for Andrey; EN: code/configs (#3)",
        "workflow": "Retrieval → Context → DAG → Execution → Memory (№13)",
        "think_in_code": "script instead of raw data in chat (#16)",
        "governance": "Fast-Track and_os/; Vault Guard Nero/ → sys_cli vault (№19)",
        "safety": "CoW snapshot before edits (#65); 3 GB disk floor",
        "discovery": "code audit -> Reuse -> Kernel Immutability (#69)"
    }


def build_domain_beacons() -> Dict[str, Dict[str, str]]:
    """The 5 architectural beacons with portable paths (no /Users/...)."""
    return {
        "1_core": {
            "name": "Core & System",
            "path": "and_os/",
            "policy": "Fast-Track edits; Zero-Blind-Assumptions (Rule #61)"
        },
        "2_vault": {
            "name": "Knowledge Vault",
            "path": "Nero/ Product/ Story/ Ta-Bu/ Clippings/",
            "policy": "Edits ONLY via sys_cli vault patch (Rule #19)"
        },
        "3_pulsar": {
            "name": "Pulsar Space",
            "path": "./pulsar/",
            "policy": "Ports :8080-:8099 (Terminal :8099); sys_cli project pulsar"
        },
        "4_xcode": {
            "name": "Xcode & Gamedev",
            "path": "./xcode/",
            "policy": "Swift 6 + SpriteKit; no code in notes (Rule #27)"
        },
        "5_comfyui": {
            "name": "ComfyUI & 3D CG",
            "path": "~/Documents/ComfyUI/",
            "policy": "LiteGraph v0.4 (extra.ds); zero ~/Downloads"
        }
    }


def parse_cg_rules_from_system_md() -> Dict[str, Dict[str, str]]:
    """Parses the SYSTEM.md rules table into {name, essence} pairs.

    Used ONLY for the CG satellite projection, which selects the rule
    names; the essence is intentionally NOT duplicated into the satellite
    (C13 F3) — the full rule text stays lazy in .opencode/rules.md, the
    same pattern as the titles-only global v2 index.
    """
    rules_dict: Dict[str, Dict[str, str]] = {}
    if not os.path.exists(SYSTEM_MD):
        return rules_dict
    with open(SYSTEM_MD, "r", encoding="utf-8") as f:
        content = f.read()

    for m in re.finditer(r'\|\s*([0-9.]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|', content):
        r_num = m.group(1).strip()
        r_name = m.group(2).strip()
        r_desc = m.group(3).strip()
        clean_desc = re.sub(r'[*_`]', '', r_desc)
        clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()
        clean_name = re.sub(r'[*_`]', '', r_name).strip()
        rules_dict[r_num] = {"name": clean_name, "essence": clean_desc}
    return rules_dict


def build_payload(compiled_sha: str) -> Dict[str, Any]:
    """Assembles the v2 session-start index payload (compact, <= budget)."""
    with open(CANONICAL_SYSTEM_JSON, "r", encoding="utf-8") as f:
        canonical_doc = json.load(f)
    rules = canonical_doc["rules"]
    return {
        "v": 2,
        "version": canonical_doc.get("version", ""),
        "compiled_at": time.strftime("%Y-%m-%d"),
        "source_sha256": compiled_sha,
        "rules_count": len(rules),
        "fulltext": ".opencode/rules.md (lazy: read the section of the rule you need)",
        "core_principles": build_core_principles(),
        "domain_beacons": build_domain_beacons(),
        "rules": {key: rule_title(text) for key, text in rules.items()}
    }


def compile_cg_satellite_projection(compiled_sha: str, cg_rules: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compiles the CG / 3D+AI domain satellite index (cg_rules_fast.json).

    C13 F3: a true fast index under the sub-core capsule contract. The
    pre-C13 payload duplicated the full rule essences here (~1700 tokens),
    breaching the <500-token budget 5.5x. Now it keeps rule numbers +
    names only and points to .opencode/rules.md for the full rule text —
    the same lazy pointer pattern as the global v2 index. Invariants and
    phase routing are kept inline (they are CG-specific and not derivable
    from the global index).
    """
    os.makedirs(os.path.dirname(CG_TARGET_JSON), exist_ok=True)

    cg_rule_keys = ["0", "0.5", "1", "3", "13", "16", "19", "27", "41", "42", "45", "57", "58", "61", "65", "68", "69"]
    # names only — the essence stays lazy in .opencode/rules.md (Rule #0)
    selected_rules = {k: cg_rules[k]["name"] for k in cg_rule_keys if k in cg_rules}

    cg_payload = {
        "domain": "cg_workspace",
        "engine": "cg_core",
        "role": "Hybrid 3D+AI Production Sub-Core",
        "compiled_at": time.strftime("%Y-%m-%d"),
        "source_sha256": compiled_sha,
        "rules_count": len(selected_rules),
        "rules": selected_rules,
        "rules_fulltext": ".opencode/rules.md (lazy: read the section of the rule you need)",
        "production_invariants": {
            "topology": "Quad-first, zero non-manifold, apply scale=1.0, pivot center-bottom",
            "hierarchy": "Max 10 semantic blocks, root_master armature",
            "linking": "Non-destructive shot assembly: Blender Library Linking & Overrides",
            "passes": "16-bit Depth, Normals, Lineart, Z-buffer, Camera POV for ComfyUI",
            "isolation": "Zero temp files in ~/Downloads or Vault root (#41)",
            "safety": "Free-First zero-cost ComfyUI nodes (#45); Air-Gap Vault Isolation (#57,#58)",
            "verification": "Anti-Beta-Tester Gate (#61): run cg_core.py qa before any report"
        },
        "production_modality_matrix": {
            "rule_of_thumb": "Blender = 3D spatial truth (Mesh/Armature/UV/Camera/Passes); ComfyUI = pixel perfection (Texture/Style/Latent/Inpainting)",
            "phase_routing": {
                "Phase_1_Blockout": "blockout_engine.py (greybox, scale=1) | kits_engine.py+Text-to-3D (silhouette) | gate: qa audit --profile game",
                "Phase_1_Shading": "uv_engine.py+materials_engine.py (PBR, clean seams) | comfy_bridge.py (texture projection, UV inpaint) | gate: zero missing UV maps",
                "Phase_2_Layout": "layout_assembler.py+previs_engine.py (Overrides, camera rail) | shot_animatic.py (I2V latent preview) | gate: animatic.meta.json + Director sign-off",
                "Phase_3_Shot": "shot_playblast_generator.py (Playblast + 16-bit Z + Normals -> ComfyUI VHS diffusion -> Resolve conform) | gate: qa review 4-way contact sheet"
            }
        }
    }

    with open(CG_TARGET_JSON, "w", encoding="utf-8") as f:
        json.dump(cg_payload, f, ensure_ascii=False, indent=1)

    size_b = os.path.getsize(CG_TARGET_JSON)
    if size_b > CG_SATELLITE_BUDGET_BYTES:
        raise ValueError(
            f"CG satellite over budget: {size_b} B > {CG_SATELLITE_BUDGET_BYTES} B — "
            f"shrink the projection payload"
        )

    return cg_payload


def compile_rules_index() -> Dict[str, Any]:
    """Compiles the v2 session-start index and the CG satellite projection.

    The serialized index is checked against SIZE_BUDGET_BYTES BEFORE
    writing: an over-budget index is a compile failure, not a warning.
    """
    compiled_sha = compute_combined_sha256()
    payload = build_payload(compiled_sha)

    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    size_b = len(serialized.encode("utf-8"))
    if size_b > SIZE_BUDGET_BYTES:
        raise ValueError(
            f"Fast index over budget: {size_b} B > {SIZE_BUDGET_BYTES} B — "
            f"shrink core_principles / domain_beacons / rule titles")

    os.makedirs(os.path.dirname(TARGET_JSON), exist_ok=True)
    with open(TARGET_JSON, "w", encoding="utf-8") as f:
        f.write(serialized)

    # Compile satellite CG projection ({name, essence} shape, no budget)
    cg_rules = parse_cg_rules_from_system_md()
    cg_payload = compile_cg_satellite_projection(compiled_sha, cg_rules)

    # Stash satellite size for the caller's report
    payload["_cg_size_b"] = os.path.getsize(CG_TARGET_JSON)
    payload["_cg_rules_count"] = cg_payload["rules_count"]
    return payload


def verify_rules_freshness() -> Tuple[bool, str]:
    """Checks both indices against the three-source sha256 and the size budget."""
    if not os.path.exists(TARGET_JSON):
        return False, f"Missing index file: {TARGET_JSON}"
    if not os.path.exists(CG_TARGET_JSON):
        return False, f"Missing satellite CG index file: {CG_TARGET_JSON}"

    try:
        current_sha = compute_combined_sha256()
        size_b = os.path.getsize(TARGET_JSON)
        if size_b > SIZE_BUDGET_BYTES:
            return False, (f"Fast index over budget: {size_b} B > {SIZE_BUDGET_BYTES} B — "
                           f"re-run compile after shrinking the payload")

        # 1. Check Global Index
        with open(TARGET_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        if current_sha != data.get("source_sha256", ""):
            return False, (f"Manifest drift in global index: source changed "
                           f"(SHA {current_sha[:8]} != {data.get('source_sha256', '')[:8]})")
        if data.get("rules_count") != len(data.get("rules", {})):
            return False, "Global index rules_count mismatch with rules dict"

        # 2. Check CG Satellite Index
        cg_size_b = os.path.getsize(CG_TARGET_JSON)
        if cg_size_b > CG_SATELLITE_BUDGET_BYTES:
            return False, (f"CG satellite over budget: {cg_size_b} B > "
                           f"{CG_SATELLITE_BUDGET_BYTES} B (sub-core capsule contract)")
        with open(CG_TARGET_JSON, "r", encoding="utf-8") as f:
            cg_data = json.load(f)
        if current_sha != cg_data.get("source_sha256", ""):
            return False, (f"Manifest drift in CG satellite index: source changed "
                           f"(SHA {current_sha[:8]} != {cg_data.get('source_sha256', '')[:8]})")

        return True, f"Rules indices fresh: Global ({data.get('rules_count', 0)}, {size_b} B) + CG Satellite ({cg_data.get('rules_count', 0)})"
    except (OSError, json.JSONDecodeError, ValueError) as e:
        return False, f"Index read error: {e}"


def status() -> int:
    """Prints index facts: size, sha, freshness, budget headroom."""
    if not os.path.exists(TARGET_JSON):
        print(f"🔴 Index missing: {TARGET_JSON}")
        return 1
    with open(TARGET_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    size_b = os.path.getsize(TARGET_JSON)
    ok, msg = verify_rules_freshness()
    print(f"Index      : {TARGET_JSON}")
    print(f"Size       : {size_b} B / budget {SIZE_BUDGET_BYTES} B (headroom {SIZE_BUDGET_BYTES - size_b} B)")
    print(f"Rules      : {data.get('rules_count', 0)} | v{data.get('v', 1)} | version {data.get('version', '?')}")
    print(f"SHA256     : {data.get('source_sha256', '?')[:16]} (3-source: SYSTEM.md + rules.md + etc/system.json)")
    print(f"CG Sat     : {CG_TARGET_JSON} ({os.path.getsize(CG_TARGET_JSON)} B)" if os.path.exists(CG_TARGET_JSON) else "CG Sat     : missing")
    print(("🟢 " if ok else "🔴 ") + msg)
    return 0 if ok else 1


def main() -> None:
    action = sys.argv[1] if len(sys.argv) > 1 else "compile"

    if action == "verify":
        ok, msg = verify_rules_freshness()
        print(f"🟢 PASS: {msg}" if ok else f"🔴 FAIL: {msg}")
        sys.exit(0 if ok else 1)

    if action == "status":
        sys.exit(status())

    if action != "compile":
        print(f"Unknown action '{action}' (use: compile | status | verify)", file=sys.stderr)
        sys.exit(2)

    try:
        payload = compile_rules_index()
    except (OSError, ValueError) as err:
        print(f"🔴 Compile failed: {err}", file=sys.stderr)
        sys.exit(1)

    size_b = os.path.getsize(TARGET_JSON)
    cg_size_b = payload.pop("_cg_size_b")
    print("✅ Rules indices compiled successfully:")
    print(f"   • Global Path: {TARGET_JSON} ({size_b} bytes / budget {SIZE_BUDGET_BYTES}, {payload['rules_count']} rules)")
    print(f"   • CG Satellite Path: {CG_TARGET_JSON} ({cg_size_b} bytes, {payload.pop('_cg_rules_count')} rules)")
    print(f"   • Source SHA: {payload['source_sha256'][:12]} (3-source)")


if __name__ == "__main__":
    main()
