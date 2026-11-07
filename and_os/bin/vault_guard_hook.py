#!/usr/bin/env python3
"""
vault_guard_hook.py — Hardware-Level PreToolUse Governance Hook (AnD os v9.0).
Implements Dual-Speed Governance (Rule #19 Invariant):
- Fast-Track (Core, Skills, System Manifests, External Projects): Allowed natively for 100% speed and token efficiency.
- Vault Guard (User Knowledge Islands: Nero/, Product/, Story/, Ta-Bu/, Book/, Clippings/, Tasks/):
  - New files via write_to_file: Allowed.
  - In-place modifications via replace_file_content: Blocked with constructive AST guidance.
"""

import sys
import json
import os

VAULT_ROOT = "."

# Dynamic configuration with static fallback
RULES_FAST_INDEX = os.path.join(VAULT_ROOT, "and_os/etc/rules_fast_index.json")

def _load_core_beacons():
    try:
        if os.path.exists(RULES_FAST_INDEX):
            with open(RULES_FAST_INDEX, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("domain_beacons", {})
    except Exception:
        pass
    return {}

_BEACONS = _load_core_beacons()

# Fast-Track prefixes (allowed to modify directly via native tools)
FAST_TRACK_EXACT = {
    os.path.join(VAULT_ROOT, "SYSTEM.md"),
    os.path.join(VAULT_ROOT, "system.json"),
    os.path.join(VAULT_ROOT, "AGENTS.md"),
    os.path.join(VAULT_ROOT, "CONTEXT.md"),
    os.path.join(VAULT_ROOT, "KNOWLEDGE.md"),
    os.path.join(VAULT_ROOT, "Vault.md"),
    os.path.join(VAULT_ROOT, "opencode.json"),
}

FAST_TRACK_PREFIXES = (
    os.path.join(VAULT_ROOT, "and_os/"),
    os.path.join(VAULT_ROOT, ".opencode/"),
    os.path.join(VAULT_ROOT, ".gemini/"),
    os.path.join(VAULT_ROOT, ".trash/"),
    "~/Yandex.Disk.localized/WORK/",
    "~/Documents/ComfyUI/",
    "/tmp/",
    "~/.gemini/",
)

# Protected User Knowledge Islands
PROTECTED_ISLANDS = (
    os.path.join(VAULT_ROOT, "Nero/"),
    os.path.join(VAULT_ROOT, "Product/"),
    os.path.join(VAULT_ROOT, "Story/"),
    os.path.join(VAULT_ROOT, "Ta-Bu/"),
    os.path.join(VAULT_ROOT, "Book/"),
    os.path.join(VAULT_ROOT, "Clippings/"),
    os.path.join(VAULT_ROOT, "Industry/"),
    os.path.join(VAULT_ROOT, "Tasks/"),
    os.path.join(VAULT_ROOT, "Studio/"),
)

# Fact Registries (Data Entities): Direct manual writes by models are strictly forbidden.
# Only deterministic Python scripts via sys_cli are allowed to create/modify files here.
FACT_REGISTRIES = (
    os.path.join(VAULT_ROOT, "Nero/profile/growth/vacancies/"),
    os.path.join(VAULT_ROOT, "Nero/profile/health/son/biomarkers/"),
    os.path.join(VAULT_ROOT, "Nero/finance/transactions/"),
)


def evaluate_tool_request(payload: dict) -> dict:
    tool_call = payload.get("toolCall", {})
    name = tool_call.get("name") or (tool_call.get("function") or {}).get("name")
    args = tool_call.get("args") or (tool_call.get("function") or {}).get("arguments") or {}

    # Intercept run_command to prevent bash bypass (cat > file, echo > file, etc.)
    if name == "run_command":
        cmd = str(args.get("CommandLine", ""))
        # Check if bash command attempts direct file redirection into protected islands
        if any(op in cmd for op in [">", ">>", "tee ", "cp ", "mv "]):
            for island in PROTECTED_ISLANDS:
                rel_island = os.path.relpath(island, VAULT_ROOT)
                if island in cmd or rel_island in cmd:
                    # Allow commands executing sys_cli vault or sys_cli tools
                    if "sys_cli" in cmd or "sys_cli.py" in cmd:
                        return {"decision": "allow"}
                    return {
                        "decision": "deny",
                        "reason": (
                            f"🚨 [RULE #19 & #56 HARDWARE BLOCK]: Direct bash redirection into vault island '{rel_island}' "
                            f"is strictly prohibited to prevent data fabrication and link corruption. "
                            f"REQUIRED: Use official CLI facade: python3 and_os/bin/sys_cli.py vault ... or tools ..."
                        )
                    }
        return {"decision": "allow"}

    # Extract target file path for filesystem tools
    target_file = args.get("TargetFile") or args.get("target_file") or args.get("path")
    if not target_file:
        return {"decision": "allow"}

    target_file = os.path.abspath(os.path.expanduser(str(target_file)))

    # 1. Fast-Track: Exact matches (system manifests in vault root)
    if target_file in FAST_TRACK_EXACT:
        return {"decision": "allow"}

    # 2. Fast-Track: Core directories, external projects, and and_os skills
    if any(target_file.startswith(p) for p in FAST_TRACK_PREFIXES):
        return {"decision": "allow"}

    # 3. Check if target resides in Protected User Islands
    is_protected = any(target_file.startswith(p) for p in PROTECTED_ISLANDS)
    if not is_protected:
        # Non-protected path outside user islands
        return {"decision": "allow"}

    rel_path = os.path.relpath(target_file, VAULT_ROOT)

    # 4. Strict Fact Registries Guard:
    # Models are NEVER allowed to use write_to_file in fact registries.
    if any(target_file.startswith(r) for r in FACT_REGISTRIES):
        return {
            "decision": "deny",
            "reason": (
                f"🚫 [RULE #56 & #61 DETERMINISTIC GUARD BLOCKED]: Direct creation/modification of data entity "
                f"'{rel_path}' by LLM is prohibited to prevent hallucinated records and broken links. "
                f"REQUIRED: Data in this registry is created strictly by official Python scripts via: "
                f"python3 and_os/bin/sys_cli.py tools career-radar ..."
            )
        }

    # 5. In User Knowledge Islands:
    # A) write_to_file creating a NEW note is allowed ONLY if file does not exist
    if name in ("write_to_file", "write_file"):
        if not os.path.exists(target_file):
            return {"decision": "allow"}
        # If file exists, overwriting completely without AST check is dangerous
        return {
            "decision": "deny",
            "reason": (
                f"🛡️ [RULE #19 GOVERNANCE BLOCKED]: Overwriting an existing vault note '{rel_path}' directly "
                f"via {name} is prohibited to prevent AST & wikilink corruption. "
                f"Use call_mcp_tool('vault-guard', 'vault_patch', ...) or "
                f"CLI: python3 and_os/bin/sys_cli.py vault patch --file '{rel_path}' --target '...' --replacement '...'"
            )
        }

    # B) replace_file_content in existing notes is blocked -> redirect to vault-guard
    if name in ("replace_file_content", "edit_file"):
        return {
            "decision": "deny",
            "reason": (
                f"🛡️ [RULE #19 GOVERNANCE BLOCKED]: Direct regex replacement in protected user note '{rel_path}' "
                f"is blocked to protect AST integrity, YAML frontmatter, and [[|...]] wikilinks. "
                f"REQUIRED ACTION: Use the AST-safe tool call_mcp_tool('vault-guard', 'vault_patch', "
                f"{{'path': '{rel_path}', 'target': '...', 'replacement': '...'}}) or "
                f"run CLI: python3 and_os/bin/sys_cli.py vault patch --file '{rel_path}' --target '...' --replacement '...'"
            )
        }

    return {"decision": "allow"}


def main():
    try:
        raw_input = sys.stdin.read().strip()
        if not raw_input:
            print(json.dumps({"decision": "allow"}))
            return

        payload = json.loads(raw_input)
        result = evaluate_tool_request(payload)
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        # Fail-safe: In case of unexpected error, allow tool execution to prevent IDE lockup
        print(json.dumps({"decision": "allow", "reason": f"Hook exception fallback: {e}"}))


if __name__ == "__main__":
    main()
