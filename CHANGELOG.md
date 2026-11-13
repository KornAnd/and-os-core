# AnD os System Changelog & Version History

> Single Source of Truth: `and_os/etc/RELEASE_LEDGER.json` (15 entries, versioned) | This file: public storefront projection.

**Current Production Version:** `v1.0.0` (2026-11-13)

---

## v1.0.0 — 2026-11-13 (MAJOR)
**Summary:** First production release of the AnD os microkernel. The 9.x development series is closed; versioning resets to the stable 1.0.0 line.
*Components:* `core`, `bin`, `lib`, `skills`

### Key Changes:
- **Self-contained functional package:** `and_os/bin/cli_subsystems/` (12 modules) and the kernel libraries (`and_os/lib/health_grid/`, `and_os/lib/vault/`, `and_os/lib/pulsar/`, `and_os/lib/xcode/`, `i1_zones.py`, `release_pipeline.py`, `apfs_shadow.py`) now ship with the release — every `and_os.*` import in the package resolves inside the package (AST-verified)
- **`quick_verify.py` runs green from a fresh clone:** standalone mode auto-skips the vault-specific Phase 7 while Phases 0–6 and 8 keep full strictness
- **`sys_cli.py audit`** runs the full 8-ring Health Grid (filesystem & syntax, knowledge graph, AST contracts & governance, clean code, manifests & security, skills, runtime, DoD)
- **76 canonical rules** (#0–#71) with compiled fast index, plus the I-1 kernel immutability zone SSoT (`and_os/etc/i1_kernel_zones.json`)
- **Privacy hardening (Zero-Leak Protocol):** the local air-gap `git` interceptor and stray runtime `and_os/var/` state artifacts removed from the public package; personal cloud-volume paths fully sanitized; exporter leak patterns extended
- **Storefront:** new README sections (Installation, Integration, When to Use AnD os), root-level CHANGELOG, version aligned across `pyproject.toml`, `system.json` and `RELEASE_LEDGER.json`

---

## v9.5.0 — 2026-11-07 (MINOR)
**Summary:** Hermetic Production Toolchain, Python 3.12.11 LTS via uv, Rule #68 Environment Parity Invariant, and Phase 0 Pre-Flight Gate
*Commit:* `sovereign_vault` | *Components:* `core`

### Key Changes:
- Пересобран и очищен Telegram-бот gorashie_nogi_bot с переходом на Python 3.12.11 и aiogram 3.31.0

---

## v9.4.0 — 2026-11-07 (MINOR)
**Summary:** Monolithic Obsidian Vault Engine (and_os/lib/vault/), Zero-Breakage Shims, MCP vault_move atomic link cascade, vfs_sentinel WebDAV hygiene hook, and Phase 3 verification guard.
*Commit:* `sovereign_vault` | *Components:* `core`

### Key Changes:
- Engineered monolithic and_os.lib.vault package (hygiene.py, graph.py, context.py, engine.py) with 100% English code/docstrings conforming to Rule #3
- Created atomic vault_move operation with WebDAV pre-flight naming validation, physical relocation, cascade [[wikilink]] refactoring across all notes, and dual-context synchronization
- Added vault_move to MCP vault-guard (vault_move.json) and CLI facade (sys_cli vault move)
- Embedded sub-0.005ms WebDAV hygiene hook into vfs_sentinel daemon (FSEvents flush_pending) with sys_bus alert emitter and 0.0% CPU footprint
- Integrated WebDAV naming hygiene validation into sys_cli verify (Phase 3: Clean Code & Vault Guard) maintaining sub-0.2s pre-flight velocity
- Enriched vault-router (v2.0) with unified lifecycle governance, eliminating agent hallucinations between file placement, naming, and link integrity

---

## v9.3.0 — 2026-11-07 (MINOR)
**Summary:** Unified 65 Skills Mesh, Remotely Save WebDAV exclusion, and trailing dot/space duplicate safe isolation.
*Commit:* `sovereign_vault` | *Components:* `core`

### Key Changes:
- Consolidated system skill registry to exactly 65 canonical active skills with sub-second SOS auditor (sys_cli skills --probe)
- Excluded and_os/ and shadow snapshots natively from Remotely Save WebDAV synchronization via deobfuscated data.json ignorePaths
- Isolated 43 trailing dot broken duplicate files to .trash/ preserving note integrity under Rule #53 Safe-Trash Policy
- Renamed 5 trailing whitespace notes and atomically refactored incoming wikilinks via sys_cli vault patch

---

## v9.2.0 — 2026-11-07 (MINOR)
**Summary:** Sovereign Systems Architect Engine and Domain Anchor Beacons.
*Commit:* `sovereign_vault` | *Components:* `core`

### Key Changes:
- Implemented Sovereign System Architecture Engine (architect_engine.py) for spec-before-code enforcement
- Established 5 Domain Anchor Beacons (Core, Knowledge Vault, Pulsar, Xcode, ComfyUI) in system prompt
- Formalized Rule #61 Zero-Blind-Assumptions verification protocol

---

## v9.1.0 — 2026-11-07 (MINOR)
**Summary:** Automated Telegram Channels Ingestion Engine and Executive Career Radar.
*Commit:* `sovereign_vault` | *Components:* `core`

### Key Changes:
- Added Automated Telegram Channels Ingestion Engine (tg_career_fetcher.py) for market and industry intel
- Implemented Executive Market Radar & Opportunity Matcher (career_radar.py)
- Bound career ingestion pipelines to official protocol Rule #59

---

## v9.0.0 — 2026-11-07 (MINOR)
**Summary:** Universal Session Gate, Hardware PreToolUse Hook, and Subagent Handoff Protocol.
*Commit:* `sovereign_vault` | *Components:* `core`

### Key Changes:
- Deployed Universal Session Gate (session_gate.py) acting as SessionStart lifecycle hook for LLM agents
- Implemented Hardware-Level PreToolUse Governance Hook (vault_guard_hook.py) enforcing Rule #19 Dual-Speed Vault Access
- Standardized Subagent Handoff Protocol (handoff) for deterministic task transfer between agents
- Integrated APFS CoW checkpoints engine (sys_cli checkpoint)

---

## v8.5.0 — 2026-11-07 (MINOR)
**Summary:** ECC Deep Integration & Autonomous Infrastructure Expansion: Continuous Learning Engine, Context Budget Guard, Build Error Resolver, Ring 5 DoD Gate, and Apple/CG Engineering Tooling.
*Commit:* `sovereign_vault` | *Components:* `core`

### Key Changes:
- Integrated Continuous Learning Engine (and_os/lib/core/continuous_learner.py + sys_cli learn): auto-extracts verified engineering patterns into Nero/knowledge/engineers/ and syncs with Clippings/quick_knowledge_db.json (Rule #48)
- Integrated Strategic Phase Compactor & Context Budget Guard (and_os/lib/core/context_budget_guard.py + sys_cli compact): tracks tool call overhead, enforces 20% reserve headroom, and issues proactive compaction reminders at Gate 2/Gate 3 transitions
- Integrated Minimal-Diff Build Error Resolver (and_os/bin/build_resolver.py + sys_cli build-fix): isolates compilation/syntax failures and guarantees atomic rollback on validation failure
- Introduced Ring 5 Definition of Done (DoD) Gate (and_os/lib/health_grid/dod_probe.py): automated verification of uncommitted secrets/keys (sk-, ghp-, AKIA), git hygiene, and asset sidecar completeness in system validator
- Added Video Harness Tool (and_os/bin/video_harness.py + sys_cli video-harness): automated technical QC for video playblasts, mod-2 dimensions, 24 FPS lock, and synthetic frame inspection
- Added Codemap AST Engine (and_os/bin/codemap_engine.py + sys_cli codemap): 0-token code architecture and hierarchy visualizer for Swift and Python across Apple/CG workspaces
- Added Project Skeleton Generator (and_os/bin/project_skeleton.py + sys_cli skeleton): standardized scaffolding for iOS SpriteKit (EscPlanet) and CG Workspace pipelines
- Added Statusline Beacon (and_os/bin/statusline.py + sys_cli statusline): single-line terminal runtime status beacon monitoring vault health, git branch, and 9/9 Island mesh connectivity

---

## v8.4.0 — 2026-11-07 (MINOR)
**Summary:** Context Budget Guard, Build Error Resolver, Codemap AST Engine, and Video QC Harness.
*Commit:* `sovereign_vault` | *Components:* `core`

### Key Changes:
- Introduced Context Budget Guard (context_budget_guard.py) enforcing 20% reserve headroom and Gate compaction
- Implemented Minimal-Diff Build Error Resolver (build_resolver.py) with atomic rollback capabilities
- Added Codemap AST Engine (codemap_engine.py) for 0-token Swift and Python code hierarchy visualization
- Added Video Harness Tool (video_harness.py) for mod-2 and 24 FPS playblast QC

---

## v8.3.1 — 2026-11-07 (MINOR)
**Summary:** Master Security & Vault Access Invariant Remediation: unified safe I/O gateway, prompt guard integration, clean architecture across opt/apps, and GDrive purge.
*Commit:* `sovereign_vault` | *Components:* `core`

### Key Changes:
- Implemented and_os/lib/core/vault_safe_io.py with atomic temp-swap, YAML frontmatter integrity, and payload ceiling control
- Refactored 20+ core and_os/bin execution engines to vault_safe_write() preventing direct unvalidated .md mutations
- Embedded canonical Vault Mutation Protocol into all 59 active skills conforming to Rule #19 invariant
- Purged 100% of silent exception handlers (except: pass) across and_os/opt/apps/ (montage_hub, cg_workspace) with structured stderr logging
- Relocated 11 technical terminal and pipeline specifications from Nero/ai/docs/ to and_os/docs/specs/ resolving Dual-Realm warning
- Sanitized non-table broken escaped wikilinks (\|) bringing Ring 1 Knowledge Graph to 100% PASS
- Completely decommissioned and unlinked external obsidian-drive-sync, setting canonical active skill registry to 59

---

## v8.3.0 — 2026-11-07 (MINOR)
**Summary:** Full ecosystem Clean Architecture overhaul (unclebob/ub-mode): zero silent exceptions, core supervisor IPC decomposition, and automated evolution gate.
*Commit:* `sovereign_vault` | *Components:* `core`

### Key Changes:
- Eliminated 100% of silent band-aids (except: pass) across and_os/ (bin, sbin, lib, opt, boot) and Pulsar workspace (227 total scripts audited)
- Decomposed CoreSupervisor (and_supervisor.py) run_loop via SRP, eliminated socket handle leaks, added strict type annotations, and reloaded macOS LaunchAgent daemon
- Refactored deep cyclomatic nesting (>4) in app_deconstructor, comfy_node_registry, and asset_indexer down to clean functional helpers
- Synchronized verified AND_Terminal codebase from Pulsar to and_os/opt/terminal
- Added Evolutionary Release Gate to Ring 3 (manifest_probe.py): enforces automatic ledger increment whenever core architecture modifications occur
- Maintained 100% APFS Zero-Cost CoW snapshot safety barriers in and_os/var/vault_shadow/

---

## v8.2.0 — 2026-11-07 (MINOR)
**Summary:** Integration of mcp-vault-guard and hybrid animatic director with Target Framework Gate.
*Commit:* `sovereign_vault` | *Components:* `core`

### Key Changes:
- Added mcp-vault-guard stdio server for AST-verified safe vault reading, patching, and frontmatter editing
- Registered vaultGuard in system.json tools and gemini mcp_config.json
- Added sys_cli.py vault read/patch/set-frontmatter command
- Enforced Vault Access Invariant in AGENTS.md and Rule #19 in SYSTEM.md
- Added Target Framework Gate (comfyui / blender / hybrid) to hybrid_animatic_director.py and sys_cli.py animatic
- Added Hermetic Workspace Boundary check in fs_syntax_probe.py (Ring 0) blocking rogue scripts in ~/Downloads
- Established RELEASE_LEDGER.json as authoritative evolution state record

---

## v8.1.0 — 2026-11-07 (MINOR)
**Summary:** Full release with Rules #0-#64, 50 skills, and multi-project decoupled architecture.
*Commit:* `sovereign_vault` | *Components:* `core`

### Key Changes:
- Decoupled Ftrack and Mattermost data pipelines
- Added Rules #55-#64
- Unified 8 Islands and terminal web console

---

## v7.6.0 — 2026-11-07 (MINOR)
**Summary:** Foundational AnD os Architecture: Initial 9-Island topology, native macOS FSEvents VFS Sentinel, SQLite metadata indexing, and Pulsar ecosystem baseline.
*Commit:* `sovereign_vault` | *Components:* `core`

### Key Changes:
- Architected initial 9 logical islands across user knowledge and system core
- Implemented native macOS FSEvents daemon (vfs_daemon) using ctypes CoreServices for sub-100ms filesystem event monitoring
- Deployed local SQLite VFS metadata index (and_os/var/vfs_state.db)
- Established Pulsar workspace (:8080-:8099) and PWA AND_Terminal console

---
