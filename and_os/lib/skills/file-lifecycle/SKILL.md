---
name: file-lifecycle
description: "Use when classifying and routing newly drafted notes, reports, and knowledge assets to their canonical Obsidian Vault folders, or updating CONTEXT.md maps, tag indexes, and wikilinks after file additions, edits, moves, or deletions."
version: "2.0.0"
lifecycle: ACTIVE
ttl: STATIC
reviewed: 2026-11-15
domain: system
island: 8
context_tier: QUICK
facade_binding: "sys_cli"
modality: EXECUTABLE_ENGINE
engine: "and_os/bin/context_router.py"
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob"]
probe_cmd: "python3 and_os/bin/context_router.py --help > /dev/null"
---
# file-lifecycle — classify ➔ route ➔ index (C11: sync-context + vault-router)

> **Purpose:** the single file-lifecycle entry point: M1 routes new notes to their canonical island (engine `context_router.py`), M2 keeps every `CONTEXT.md` map, tag index, and wikilink in sync (engine `sync_context.py`, dispatcher alias `sys_cli sync`).

## M1: Route (classify & persist a new note)

**Inbound scope:** the whole Vault (read/analysis). **Outbound writes:** strictly isolated to the designated domain island within `Nero/` (or `and_os/` for core system code/configs). Rule №7.
**STRICT PROHIBITION OF FALSE DEFAULT:** dumping "by default" into `Nero/ai/docs/` is forbidden (reserved exclusively for AI architecture specs, deployment guides, model benchmarks). Ambiguous destination ➔ **Clarification Gate** (proactively ask, suggest 2–3 candidates). Creating new root directories without explicit instruction is forbidden.

### Domain Routing Matrix (Persistence Scope)
| Keyword Context in Request | Classification | Canonical Destination |
|---|---|---|
| "AI spec", "architecture guide", "deployment", "AI models" | Architectural AI specs | `Nero/ai/docs/` |
| "script", "utility", "CLI tool", "automation" | System executable code | `and_os/bin/` |
| "configuration", "schema", "system registry" | System config & schemas | `and_os/etc/` |
| "article", "post", "CG_core", "VK", "consulting" | Brand content & essays | `Nero/cg_core/` |
| "analysis"/"status"/"production plan" + Mars \| Kot | Feature analytics | `Nero/work/<project>/analytic_<project>/` |
| "standup", "follow-up", "chat log", "meeting notes" | Operational team updates | `Nero/work/<project>/info_<project>/` |
| "task", "Weeek", "Ftrack" | Project tracking tasks | `Nero/work/<project>/tasks_<project>/` |
| "team", "RnD", "Studio", "pipeline output" | Studio Production / RnD | `Nero/work/rnd/` or `Nero/work/Studio/` |
| "script", "logline", "story", "synopsis" | Narrative IP & Screenplays | `Nero/story/` (ChudoBus: `chbs/`) |
| "book", "summary", "literature notes" | Books & study summaries | `Nero/book/` |
| "investing", "portfolio", "broker_account", "Alfa" | Wealth & financial portfolios | `Nero/profile/finance/` |
| "taxes", "NPD", "Sole Proprietorship", "receipts" | Fiscal & tax compliance | `Nero/profile/finance/tax/` |
| "health", "lab tests", "diagnostics", "therapy" | Personal & family health | `Nero/profile/health/my/` or `family/<person>/` |
| "training", "endurance", "marathon", "Ironman", "gear" | Athletic training | `Nero/profile/sport/` |
| "goals", "strategy", "identity", "CV" | Personal growth & strategy | `Nero/profile/growth/` |
| "prompt", "workflow", "ComfyUI", "generation" | Generative AI assets | `Nero/ai/` |
| "skill", "agent skill" | AnD os system skill | `and_os/lib/skills/<skill-name>/` |
| "Ta-Bu", "startup", "investor pitch", "SaaS" | Ta-Bu Studio startup | `Nero/ta_bu/` (software: `soft/`) |
| "general", "real estate", "mac cheat sheet" | General reference | `Nero/other/` |
| "application source", "docker", "fastapi backend" | Standalone app code | `~/Pulsar_Apps/` (outside Vault) |

### Canonical File Header (mandatory)
Frontmatter: `created/updated` (YYYY-MM-DD HH:mm) · `type: knowledge|task|project|log` · `tags: [ai, <domain_1>, <domain_2>]` · `project: <id|general>` · `status: draft|in_progress|approved` · `links: ["[[Doc_1]]"]`. Plus passport lines: `> **Date**: … | **Project**: [[…]] | **Status**: …` and `> **Focus**: <concise operational objective>`.

### Pipeline
1. Deduce domain from content + prompt ➔ match the routing matrix.
2. **WebDAV Hygiene Pre-flight:** no trailing dot/space, no `< > : " | ? *`, UTF-8 length < 200 bytes.
3. Unambiguous ➔ scaffold with Canonical Header and write. Ambiguous ➔ Clarification Gate (never guess blindly).
4. Register immediately in parent `CONTEXT.md` (0% orphan notes); **Semantic Relation Linking:** `python3 and_os/bin/sys_cli.py relate "<new_file_path>"` ➔ top-3 related documents ➔ wikilinks into `links:`.
5. Never write ad-hoc notes into `Product/Projects/…`, `Story/`, `Tasks/` without explicit instruction; never write outside the Vault; moves only via `vault_move` / `sys_cli vault move <src> <dst>` (cascades all incoming wikilinks + syncs both CONTEXT.md).

## M2: Index (CONTEXT.md sync after additions/edits/moves/deletions)
Engine: `python3 and_os/bin/sync_context.py --check|--fix [--path <target_dir>]` (dispatcher alias: `python3 and_os/bin/sys_cli.py sync [--check|--fix]`). Trigger phrases: "added material / new files / update indexes".
1. Locate changed directory `X/`; ensure `X/CONTEXT.md` exists (scaffold from `references/context_template.md` or `references/note_template.md`).
2. **Ingestion:** insert `### [[filename|filename.md]] — 1-line description` under Files or Subdirectories.
3. **Tags & Links audit:** validate frontmatter `tags:` (append domain tags inherited from `X/CONTEXT.md` additively — never purge meaningful tags); ensure backlink footer to parent index.
4. **Deletion** ➔ prune obsolete links; **Rename** ➔ update `[[wikilink]]` targets and labels.
5. `Clippings/` touched ➔ recompile `Clippings/quick_knowledge_db.json` (Rule №9.5).
6. Refresh `*Updated: YYYY-MM-DD*`; `Nero/` paths ➔ propagate to [[Nero/CONTEXT]].

## Verification Checklist
- [ ] Destination strictly within `Nero/` (or `and_os/` for core); no Desktop/Downloads/tmp escapes
- [ ] Filename WebDAV-clean; mandatory frontmatter + passport header populated
- [ ] Semantic relations checked via `sys_cli.py relate`; navigation backlink appended
- [ ] Target `CONTEXT.md` valid after modification; all active files indexed; all wikilinks resolve
- [ ] New notes carry domain tags + parent backlink; timestamp refreshed; `Nero/CONTEXT` synchronized

## Anti-Triggers & Constraints
- Never delete `CONTEXT.md` even when the folder is temporarily empty; do not touch `.space/`, `.obsidian/`, `.trash/`
- Never append wikilinks targeting binary assets; never overwrite existing user tags (append additively)
- Never rename/move notes with raw `mv` — `vault_move` only

## Vault Mutation Protocol (Rule #19 Invariant)
- Reading, patching, metadata: `mcp-vault-guard` tools (`vault_read`, `vault_patch`, `vault_set_frontmatter`) or `python3 and_os/bin/sys_cli.py vault [read|patch|set-frontmatter]`.
- Renaming/moving: `vault_move` or `sys_cli vault move` — guarantees WebDAV compliance + wikilink cascade + both CONTEXT.md sync.
- Zero syntax corruption in wikilinks (pipe characters) and YAML frontmatter symmetry.
