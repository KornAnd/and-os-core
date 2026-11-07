---
name: ROUTING
description: "Central skill routing atlas: domain -> core skills -> file scopes -> on-demand extension skills. Governed by 7 Logical Islands and cross-island bridges."
tags:
  - nero
  - skills
  - system
  - routing
lifecycle: ACTIVE
ttl: STATIC
version: 2.1.0
reviewed: 2026-10-19
---

# ROUTING — Domain → Core → Scope → Extensions

**Central Routing Specification.** Replaces isolated keyword guesswork with a disciplined two-tier model:

1. **Task Domain** (Primary — Rule №0.5).
2. **Domain Core** — Default primary skills activated FIRST.
3. **Operational Scope** — Filesystem directories where domain assets and state reside.
4. **Extensions** — Secondary supporting skills loaded strictly on-demand or upon explicit prompt.

Invariant: **Core first. Extension only if the task demands it** (specialized artifact type, narrow query, or auxiliary validation step). Never scan all 50 skills indiscriminately — inspect only the target domain core + relevant extension.

---

## 9 Logical Islands & Skill Topography

All domains and skills map directly to the **9 Logical Islands** (`[[and_os/etc/ISLANDS_ROUTER|ISLANDS_ROUTER.md]]`), interconnected via cross-island transit bridges:

| Island | Domain Focus | Core (Primary, Default First) | File Scopes | Extensions (On-Demand) | Cross-Island Bridges |
|:---:|---|---|---|---|---|
| **Island 1** | **Knowledge Base (Clippings & CG Articles)** | `clipping-finder` / `cg-article` | `Clippings/`, `Tags/`, `CG_core/Статьи/` | `book-summary-practical`, `book-hub` | 🌉 Accessible across ALL islands for industry grounding and proven frameworks |
| **Island 2** | **Consulting & Media (CG_core)** | `cg-content-factory` / `cg-article` | `CG_core/` (incl. `Статьи/`), `Industry/`, `Nero/cg_core/` | `cg-core-consulting`, `clipping-finder` | 🌉 Ingests case studies from **Island 5** (Studio); transfers B2B enterprise leads to **Island 3** (Ta-Bu) |
| **Island 3** | **Startup Incubator (Ta-Bu)** | `ta-bu-plan` | `Ta-Bu/`, `Nero/ta_bu/` | `investor-outreach`, `negotiation`, `budget-calculator` | 🌉 Incubates software products for **Island 7** (Pulsar); sources narrative IP from **Island 4** (Story) |
| **Island 4** | **Narrative & Books (Story / Book)** | `story-dev` / `book-hub` | `Story/`, `Book/`, `Nero/story/` | `hybrid-animatic-director`, `script-bible-extractor`, `clipping-finder`, `higgsfield-seedance-prompt` | 🌉 Supplies shot explications and asset bibles directly to **Island 7** (3D Pulsar & CG) |
| **Island 5** | **Studio Production (Studio)** | `status-report` / `ftrack-sync` | `Product/Projects/*`, `Studio/`, `Tasks/` | `postmortem-analyzer`, `meetings-hub`, `employee-hub`, `weeek-hub`, `mattermost-sync`, `board-analyzer` | 🌉 Hands off shot specifications to **Island 7**; supplies empirical case studies to **Island 2** |
| **Island 6** | **Governor & Health (Nero Core)** | `sys_cli.py` / `health-diagnostics-hub` | `Nero/profile/`, `and_os/lib/skills/`, `Nero/ai/` | `portfolio-summary`, `tax-compliance`, `task-graph`, `system-audit`, `goal-writer`, `decision-log`, `endurance-training-plan`, `telemetry_sync`, `uc-diet-planning`, `career-radar`, `executive-mirror` | 🌉 Central Governor: monitors health, personal strategy, wealth, career radar, rule governance, and hardware resources |
| **Island 7** | **Engineering & 3D (Pulsar Apps & CG)** | `cg-pipeline` (`cg_core.py`) / `dev-flow` | `and_os/opt/apps/`, `pulsar/shared/`, `cg_workspace/` | `editorial-otio-conform`, `hybrid-comfyui-render`, `temporal-consistency-guard`, `api-contract-generator`, `comfy-builder`, `ui-inspector`, `app-bridge`, `openmontage-builder`, `higgsfield-seedance-prompt` | 🌉 Ingests storyboards from **Island 4**; delivers real-time production dashboards to **Island 5** |
| **Island 8** | **System Core & Terminal (and_os)** | `sys_cli.py` / `system-architect` | `and_os/bin/`, `and_os/opt/terminal/` | `clean-code-guardian`, `obsidian-bases`, `external-skills-gateway`, `github-ops`, `skill-creator`, `skill-router`, `context-compressor` | 🌉 Sovereign microkernel, rules compiler, and AST governance controlling system bus across all islands |
| **Island 9** | **Mobile App & Game Engineering (Xcode / iOS)** | `ios-game-builder` | `Nero/xcode/`, `WORK/xcode/` | `swift`, `xcodebuild`, `xcrun simctl` | 🌉 Ingests 2D/3D sprites from **Island 7**; narrative from **Island 4**; MVP tracking from **Island 3**; dev accounts from **Island 6** |

---

## Universal Meta-Skills (Cross-Domain Dynamic Loading)

| Skill | Activation Trigger |
|-------|--------------------|
| `task-graph` | Any complex or multi-phase task (DAG compilation, skill/script binding, Mermaid rendering, Canvas export, swimlane concurrency) |
| `dev-flow` | Software engineering, bug fixes, refactoring across Pulsar and `and_os/` (modular pipeline, test-driven validation, Stop-on-3 circuit breaker) |
| `app-deconstructor` | Reverse engineering and architecture deconstruction of unfamiliar apps, services, and codebases into C4 blueprints |
| `llm-council` | High-stakes architectural or product decision-making, pressure-testing alternatives (5-persona advisory council with veto checks) |
| `document-hub` | Ingestion and OCR parsing of PDF, Excel, Word, PPTX, or image text via MarkItDown across any domain |
| `yt-analyze` | Analysis and transcript extraction for YouTube URLs across any domain |
| `prompt-improver` | Raw or voice-dictated prompts transformed into structured 5-block prompt specifications |
| `negotiation` | High-stakes dialogue, contract negotiations, budget defense, stakeholder feedback |
| `clipping-finder` | Fallback retrieval when domain triggers are ambiguous — queries the 229-book knowledge base |

---

## Standard Execution Pipelines (Macro-Chains)

When an objective demands orchestration across multiple skills, adhere to established pipeline standards. Never maintain chain state solely in ephemeral context — persist state at each gate:

### 1. Health & Athletic Performance Pipeline
```
[New lab panels / Clinical reports / PDF / Biomarkers]
       │
       ▼
1. health-diagnostics-hub (telemetry extraction, clinical grounding, prescription verification)
       │  ➔ Artifact: Nero/profile/health/<patient>/<patient>_diagnostics.md
       ▼
2. medical_gate.md (numeric safety thresholds: ferritin, TSH, resting HR, inflammation)
       │  ➔ Status: CLEARED / RESTRICTED / CLINICAL_REVIEW
       ▼
3. endurance-training-plan (calibrate training volume, heart rate zones, Half Ironman periodization)
       │  ➔ Artifact: Weekly training schedule / microcycle plan
       ▼
4. telemetry_sync (benchmark actual autonomic adaptation: resting HR, HRV, sleep quality, Body Battery)
```

### 2. Studio Production Management Pipeline
```
[Production task tracker data / Weekly milestone quota]
       │
       ▼
1. ftrack-sync (CSV export ➔ local parser ➔ shot/asset/latency analytical delta)
       │  ➔ Artifact: Nero/work/<project>/ftrack_status_*.md
       ▼
2. status-report (executive multi-department audit: progress trends, single points of failure)
       │  ➔ Artifact: Product/Projects/<project>/Analysis_*.md
       ▼
3. weeek-hub (sprint board synchronization and task grooming)
       │  ➔ Verified action items
       ▼
4. meetings-hub (structured meeting minutes with assigned owners and hard deadlines)
```

### 3. Thought Leadership & Content Pipeline
```
[Thesis topic / Industry bottleneck / Core insight]
       │
       ▼
1. clipping-finder (query proven models and literature in Clippings/)
       │  ➔ Extracted frameworks and citations
       ▼
2. story-dev / cg-article (dramaturgy: 3-act structure, hook, narrative tension, actionable conclusion)
       │  ➔ Draft article in Russian
       ▼
3. cg-article (Mode 2: translation and adaptation into executive conversational English for LinkedIn)
       │  ➔ EN article version
       ▼
4. vault-router ➔ sync-context (persist in CG_core/Статьи/ and update CONTEXT.md navigation maps)
```

### 4. Startup & Venture Incubation Pipeline
```
[Product initiative / Commercial lead / Investor outreach]
       │
       ▼
1. ta-bu-plan (12-domain audit, unit economics, strategic milestone roadmap)
       │  ➔ Calibrated startup master plan
       ▼
2. budget-calculator (production budget, shot quota, resource breakdown)
       │  ➔ Financial ledger model
       ▼
3. investor-outreach (personalized pitch deck, institutional grant/venture proposal)
       │  ➔ Formal communication draft
       ▼
4. negotiation (interest polyhedron mapping, objection redirection, Sun Tzu / Voss tactical tools)
```

### 5. System Maintenance & Autonomous Healing Pipeline
```
[Scheduled maintenance or significant architectural refactoring]
       │
       ▼
1. system-audit (deep audit across 6 Rings of Health Grid: AST contracts, links, version drift, manifests)
       │  ➔ Diagnostics report in and_os/var/system_health.json
       ▼
2. sync_context.py (automatic validation and link repair across 48 CONTEXT.md files)
       │  ➔ Synchronized navigation topology
       ▼
3. telemetry (record calibrated telemetry metrics in telemetry.md)
```

### 6. 3D & Hybrid CG Production Pipeline
```
[Concept art / Sketch / Production asset specification]
       │
       ▼
1. task-graph (DAG task decomposition, ID binding, concurrency swimlanes)
       │  ➔ DAG plan and milestone control matrix
       ▼
2. cg-pipeline / asset_builder (procedural mesh generation, 10-bone armature rigging, material setup)
       │  ➔ DoD Gate 1: validator.py (Scale=1, Armature Standards, zero missing libs)
       ▼
3. layout_assembler (shot assembly, Library Overrides, camera lens setup 24/35/50/85mm)
       │  ➔ DoD Gate 2: external link integrity verification
       ▼
4. comfy-builder / comfy_bridge (hybrid generative validation: Depth/Normal pass checks, PBR textures)
       │  ➔ DoD Gate 3: form and consistency verification (Low-VRAM / Offline headless mode)
       ▼
5. preview_delivery (render frame preview, emit chat report, GUI strictly On-Demand)
```

---

## Cross-Domain Competency Transfer Matrix

When Andrey applies professional mastery from one domain to another, enforce data isolation boundaries:

| Competency Source (Donor) | Target Domain (Recipient) | Transferred Frameworks & Skills | Data Isolation Boundary |
|---|---|---|---|
| **Studio (Production)** | **Ta-Bu Studio (Startup)** | `budget-calculator` (estimates), `status-report` (reporting structure), `employee-hub` (grading model) | **Commercial Isolation:** Transfer formulas, logic, and milestone structures; strictly prohibit leaking confidential studio artist rates or signed studio contracts. |
| **Studio (System)** | **CG_core (Consulting/Brand)** | `system-audit`, `sync-context`, studio pipeline standards | **Generalization:** Insights delivered as anonymized principles and architectural models without studio NDA details. |
| **Narrative (Story)** | **Ta-Bu (IP/SaaS) & Book** | `story-dev` (3-act structure, loglines, character arcs) | **Unified Canon:** Narrative universes (ChudoBus, Zhest) develop synchronously across script, pitch deck, and book drafts. |
| **Negotiation (Skills)** | **Universal Across All Domains** | `negotiation` (Harvard model, Voss, OODA, stratagems) | Pervasive competency: deployed when pitching Ta-Bu investors, aligning studio leads, or closing education partners. |
| **Personal Strategy (Growth)** | **All Projects (P1–P5)** | `strategy-review` (25-goal balancing) | Synchronizes weekly operational focus in `Diary/` with overarching 20-year roadmap. |

**Governing Transfer Law:** *«Transfer the algorithm, structure, and mental model, but keep empirical data of each project strictly isolated.»*

---

## Execution Guide for Autonomous Agents

```
Task Received
 └─ 1. IDENTIFY domain (from 7 Logical Islands above)
 └─ 2. LOAD domain core skills (core skills are immediate candidates)
 └─ 3. SELECT single primary skill matching the narrowest objective (Rule №12)
 └─ 4. If core is insufficient (specialized artifact type) → ATTACH extension skill
 └─ 5. Universal tools (OCR / Excel / YT / Prompt) → load strictly on-demand
 └─ 6. Ambiguous domain/trigger → fallback to clipping-finder
```

---

## Anti-Triggers & Invariants

- Once a domain is identified, skills belonging to UNRELATED domains must not be triggered solely due to coincidental keyword matches.
- If domain core covers the scope, do NOT attach extension skills.
- If domain data files are absent from prompt and context, do not invoke domain skill (Context Gate).

---

## Meta & System Skills Cross-Domain Matrix

All 50 skills across the architecture are fully mapped to their respective Islands and execution tools:

| Skill | Architectural Role / Domain | Island Binding | Tool / Execution Script | Triggers & Keys |
| :--- | :--- | :---: | :--- | :--- |
| `skill-router` | Primary arbiter for selecting Primary skill | ⚡ Island 8 / Core | `and_os/lib/skills/ROUTING.md` | select skill, task route, routing |
| `skill-creator` | Ring 0 canonical meta-skill & compiler for skills | ⚡ Island 8 / Core | `and_os/lib/skills/skill-creator/` | create skill, validate skill, lint skill, skill ABI |
| `context-compressor` | Context budget compression (Rule №44) | ⚡ Island 8 / Core | `and_os/bin/context_bundler.py` | compress context, context budget, bundle |
| `knowledge-promoter` | Promotes artifacts to L2/L3 knowledge base | 📚 Island 1 | `and_os/bin/sync_context.py` | save knowledge, promoter, crystallize |
| `decision-log` | Persists architectural and product ADRs | 🚀 Island 3 / 6 | `Nero/profile/my/decision_log.md` | decision log, ADR, record choice |
| `goal-writer` | Formulates 100 life and quarterly goals | 🧠 Island 6 | `Nero/profile/growth/goals/` | goal, SMART goals, 100 goals, annual plan |
| `project-state` | Captures operational delta snapshot of project | 🎬 Island 5 | `and_os/bin/state_manager.py` | project state, delta, sprint status |
| `mattermost-sync` | Channels summarization in Mattermost | 🎬 Island 5 | `and_os/bin/mattermost_sync.py` | mattermost chats, team sync, channel digest |
| `board-analyzer` | Parses and analyzes task boards (Weeek/Trello) | 🎬 Island 5 | `and_os/bin/board_parser.py` | task board, kanban, task blockers |
| `app-bridge` | Bridge between Obsidian and Pulsar apps | 💻 Island 7 | `and_os/bin/app_bridge.py` | app bridge, connect web app, blueprint |
| `openmontage-builder` | Autonomous video editing studio (FFmpeg) | 💻 Island 7 | `and_os/lib/skills/openmontage-builder/` | video editing, assemble clip, video script |
| `higgsfield-seedance-prompt` | Neural animation and video prompts | 💻 Island 7 | `and_os/lib/skills/higgsfield-seedance-prompt/` | seedance, video prompt, video generation, higgsfield |
| `ai-rule` | Validates system rules and compiles prompts | ⚡ Island 8 | `.opencode/rules.md` | AI rule, system prompt, rule validation |
| `teach-hub` | Interactive pedagogical trajectory | 🎙️ Island 2 | `Industry/Game4Art/` | teach me, learning path, step-by-step lesson |
| `uc-diet-planning` | Medical menu and nutritional protocol for UC | 🧠 Island 6 | `Nero/profile/health/family/son/` | UC diet, Misha menu, gut soothing diet |
| `obsidian-drive-sync` | One-way sync of vault to Google Drive | ⚡ Island 8 | `and_os/bin/obsidian_drive_sync.py` | cloud backup, drive copy, drive sync |
| `health-orchestrator` | Holistic health synthesis, training clearance | 🧠 Island 6 | `Nero/profile/health/` | health synthesis, training clearance, biomarker cross-analysis |

---

## Registry Links

- [[and_os/lib/skills/CONTEXT|Full skills registry map]]
- [[and_os/lib/skills/README|Skill creation and lookup specification]]
- [[KNOWLEDGE|Global knowledge topology]]
- [[Nero/CONTEXT|Nero domain root atlas]]
