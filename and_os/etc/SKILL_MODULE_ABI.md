# 🧩 SKILL_MODULE_ABI v2.1 — Universal Skill & Module Specification (AnD os v1.1.0)

> 💡 **TL;DR:** Canonical Application Binary Interface (ABI) for all 50 system skills in AnD os. Standardizes execution contracts, declarative reference extraction, pipeline chaining, and atomic registration across the 9 logical islands.
> 📅 **Revision Date:** 2026-11-18 | **Status:** CANONICAL | **Rule Alignment:** Rules #16, #40, #42, #50, #51, #54, #55
> **Relationship:** this document is the full reference (SSoT, `and_os/etc/`). The compact lint-enforced subset — validated by `skill-creator/scripts/validate_skill.py` — is mirrored at `and_os/lib/skills/skill-creator/references/SKILL_MODULE_ABI_SPEC.md`; keep both in sync on any ABI change.

---

## 🏛️ 1. Conceptual Framework & Dual Modality

Every skill residing in `and_os/lib/skills/<name>/` functions as a recognized system module with one of two primary operational modalities:

Modality describes **what the skill module itself owns**; engine linkage lives in `and_os/etc/SKILL_BINDINGS.json` (the `engine:` field there is a binding, not a modality).

1. **`EXECUTABLE_ENGINE` (Active Computation):**
   - Owns executable logic: Python scripts in `and_os/lib/skills/<name>/scripts/` (must then ship a `scripts/canary.py` smoke probe, <500 ms) or a dedicated runner declared via the frontmatter `engine:` field.
   - Executes deterministic data transformations, API caching, file I/O, or rendering.
   - Must expose standard CLI flags: `--json`, `--out`, `--help`.
   - Exit code `0` strictly signals success. Output on stdout should be machine-readable when `--json` is supplied.
   - Example: `cut-suite`, `deep-research`, `houdini-bridge`, `system-audit` (all with `scripts/`).

2. **`DECLARATIVE_KNOWLEDGE` (Cognitive & Methodological Protocol):**
   - High-fidelity guidance, decision matrices, clinical rules, and strategic frameworks.
   - Does not maintain a physical executable runner in the skill folder; instead, supplies structured knowledge models to the LLM agent.
   - May be facade-bound to a shared `and_os/bin/` engine via `SKILL_BINDINGS.json` without changing its modality (e.g. `ftrack-sync` → `and_os/bin/ftrack_sync.py`).
   - Contains a rich `references/` directory organized by topical headers.
   - Example: `negotiation`, `health-hub`, `ai-rule`, `story-dev`, `ftrack-sync` (engine-bound).

---

## 📋 2. Frontmatter Contract (ABI v2.1)

Each `SKILL.md` MUST define the following minimum frontmatter schema:

```yaml
---
name: <kebab-case-name>               # Unique skill identifier matching directory name
description: "Use when ..."            # Machine-discoverable trigger: observable situation + intent
version: 1.0.0                         # Independent module SemVer (Rule #55)
lifecycle: ACTIVE                      # ACTIVE | EXPERIMENTAL | REVIEW | DEPRECATED | ARCHIVED
ttl: STATIC                            # STATIC | SEMI-STABLE | VOLATILE
reviewed: YYYY-MM-DD                   # Last architectural audit date
probe_cmd: "<canary-check-command>"    # Canary must complete < 500 ms (probe hard timeout: 3 s)
---
```

The description MUST begin with `Use when` — an observable situation and intent (this is the harness routing trigger; see `skill-creator` §6 Routing Eval Protocol for the admission gate on description changes).

---

## ⚡ 3. Microkernel Skill Bus Interface (`skill_bus.py`)

All interactions with skills MUST pass through the unified Microkernel Skill Bus (Rule #51):

### A. Execution Protocol (`run`)
```bash
python3 and_os/bin/sys_cli.py skill run <skill_name> [flags/args] [--json]
```
- Locates the bound engine in `SKILL_BINDINGS.json` (fallback: `and_os/bin/<name>.py`).
- Injects standard telemetry tracking upon completion.
- Truncates oversized stdout stream if exceeding 150 lines (Rule #44), preserving JSON payloads.

### B. 0-Token Reference Extractor (`ref`)
```bash
# List available reference documents and sections:
python3 and_os/bin/sys_cli.py skill ref <skill_name> --list

# Extract specific topic without loading extraneous tokens:
python3 and_os/bin/sys_cli.py skill ref <skill_name> --topic "<topic_slug_or_header>"
```
- Extracts only target Markdown sections bounded by headers.
- Eliminates context bloating, saving up to 95% of LLM prompt tokens.

### C. Pipeline Data Chaining (`pipe`)
```bash
python3 and_os/bin/sys_cli.py skill pipe <producer_skill> <consumer_skill> --args '...'
```
- Executes `<producer_skill>` with `--json`.
- Validates the JSON output; pipes the payload into the input argument of `<consumer_skill>`.

---

## 🔒 4. Atomic Registration Invariant (Rule #54 & #55)

The addition of any new skill module MUST be atomic and transactional:
1. Directory created in `and_os/lib/skills/<name>/`.
2. Symlink linked in the vault's `.opencode/skills/<name>` (harness pickup).
3. Skill bound in `and_os/etc/SKILL_BINDINGS.json`.
4. Global counter synchronized across all system manifests (`system.json`, `SYSTEM.md`, `AGENTS.md`, `and_os/etc/SYSTEM_MAP.md`, `and_os/etc/SYSTEM_ARCHITECTURE_GRAPH.md`, `and_os/lib/skills/README.md`) via `skill-creator/scripts/sync_system_mesh.py`.
5. Verified via the SOS Multi-Core Probe (Ring 3.5): `python3 and_os/bin/sys_cli.py audit --json` (probe `skill`).
6. In case of any probe failure, the change is rolled back before the session ends.

---
[[Vault|← Vault]]
