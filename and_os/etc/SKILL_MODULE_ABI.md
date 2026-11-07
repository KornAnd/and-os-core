# 🧩 SKILL_MODULE_ABI — Universal Skill & Module Specification (AnD os v8.1)

> 💡 **TL;DR:** Canonical Application Binary Interface (ABI) for all 58 system skills in AnD os. Standardizes execution contracts, declarative reference extraction, pipeline chaining, and atomic registration across all 8 islands.  
> 📅 **Revision Date:** 2026-10-23 | **Status:** CANONICAL | **Rule Alignment:** Rules #16, #40, #42, #50, #51, #54, #55

---

## 🏛️ 1. Conceptual Framework & Dual Modality

Every skill residing in `and_os/lib/skills/<name>/` functions as a recognized system module with one of two primary operational modalities:

1. **`EXECUTABLE_ENGINE` (Active Computation):**
   - Backed by an optimized Python script in `and_os/bin/` or `and_os/lib/skills/<name>/scripts/`.
   - Executes deterministic data transformations, API caching, file I/O, or rendering.
   - Must expose standard CLI flags: `--json`, `--out`, `--help`.
   - Exit code `0` strictly signals success. Output on stdout should be machine-readable when `--json` is supplied.
   - Example: `editorial-otio-conform`, `hybrid-animatic-director`, `ftrack-sync`, `sync-context`.

2. **`DECLARATIVE_KNOWLEDGE` (Cognitive & Methodological Protocol):**
   - High-fidelity guidance, decision matrices, clinical rules, and strategic frameworks.
   - Does not maintain a physical executable runner; instead, supplies structured knowledge models to the LLM agent.
   - Contains a rich `references/` directory organized by topical headers.
   - Example: `negotiation`, `health-diagnostics-hub`, `ai-rule`, `story-dev`.

---

## 📋 2. Frontmatter Contract (ABI v2.1)

Each `SKILL.md` MUST define the following minimum frontmatter schema:

```yaml
---
name: <kebab-case-name>               # Unique skill identifier matching directory name
description: "[Category] Purpose..." # Machine-discoverable description with domain prefix
tags:
  - nero
  - skills
  - <domain>
lifecycle: ACTIVE                     # ACTIVE | EXPERIMENTAL | REVIEW | DEPRECATED | ARCHIVED
ttl: STATIC                           # STATIC | SEMI-STABLE | VOLATILE
version: 1.0.0                        # SemVer specification
reviewed: YYYY-MM-DD                  # Last architectural audit date
probe_cmd: "<canary-check-command>"   # Lightweight execution check (timeout <= 500ms)
---
```

---

## ⚡ 3. Microkernel Skill Bus Interface (`skill_bus.py`)

All interactions with skills MUST pass through the unified Microkernel Skill Bus:

### A. Execution Protocol (`run`)
```bash
python3 and_os/bin/sys_cli.py skill run <skill_name> [flags/args] [--json]
```
- Locates the bound engine in `SKILL_BINDINGS.json`.
- Injects standard telemetry tracking upon completion.
- Truncates oversized stdout stream if exceeding 150 lines (Rule #44), preserving JSON payloads.

### B. 0-Token Reference Extractor (`ref`)
```bash
# List available reference documents and sections:
python3 and_os/bin/sys_cli.py skill ref <skill_name> --list

# Extract specific topic without loading extraneous tokens:
python3 and_os/bin/sys_cli.py skill ref <skill_name> --topic "<topic_slug_or_header>"
```
- Extracts only target Markdown sections bounded by H2/H3 headers.
- Eliminates context bloating, saving up to 95% of LLM prompt tokens.

### C. Pipeline Data Chaining (`pipe`)
```bash
python3 and_os/bin/sys_cli.py skill pipe <producer_skill> <consumer_skill> --args '...'
```
- Executes `<producer_skill>` with `--json`.
- Validates the JSON output against schema contracts.
- Pipes the payload into the input argument of `<consumer_skill>`.

---

## 🔒 4. Atomic Registration Invariant (Rule #54 & #55)

The addition of any new skill module MUST be atomic and transactional:
1. Directory created in `and_os/lib/skills/<name>/`.
2. Symlink linked in `~/.opencode/skills/<name>`.
3. Skill bound in `and_os/etc/SKILL_BINDINGS.json`.
4. Global counter synchronized across all 4 system manifests:
   - `AGENTS.md`: `реестр {N} скиллов`
   - `and_os/etc/SYSTEM_MAP.md`: `{N} Active Skills`
   - `and_os/etc/SYSTEM_ARCHITECTURE_GRAPH.md`: `{N} Active Skills`
   - `and_os/lib/skills/README.md`: `{N} active skills`
5. Verified via SOS Multi-Core Auditor (`python3 and_os/bin/sys_cli.py skills --probe`).
6. In case of any probe failure, an automatic rollback (revert) is triggered immediately.

---
[[|[[Vault|← Vault]]
