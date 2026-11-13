---
tags:
  - system
  - toolchain
  - context
  - runtime
created: 2026-11-11 22:36:20
---

# 🛠️ SYSTEM TOOLCHAIN — Runtime Standard & Toolchain Specification AnD os v1.0.0

> **Specification for AI Agents and Developers:** Canonical specification of programming language versions, installed libraries, 113 core scripts, and 67 active skills.  
> **Automated Refresh:** `python3 and_os/bin/sys_cli.py env` or `python3 and_os/bin/system_tools_map.py --build`

---

## ⚙️ 0. Runtime Environment Standard

| Language / Runtime | Current Version | Target Standard | Executable Path | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Python** | `3.12.11` | `>=3.11 (Recommended 3.14.x)` | `./and_os/.venv/bin/python` | 🟢 Active |
| **Node.js** | `v26.13.0` | `>=20.x LTS` | `Node Runtime (Homebrew)` | 🟢 Active |
| **Deno** | `deno 2.9.8 (stable, release, aarch64-apple-darwin)` | Modern TS/JS Runtime | `Deno (Homebrew)` | 🟢 Active |
| **Go** | `go version go1.27.3 darwin/arm64` | Compiled Backend Runtime | `Go (Homebrew)` | 🟢 Active |
| **Swift** | `Apple Swift version 6.4 (swiftlang-6.4.0.34.1 clang-2100.3.34.1)` | Native Apple Ecosystem | `Apple Swift 6 Toolchain` | 🟢 Active |
| **Git** | `git version 2.54.0 (Apple Git-157)` | `>= 2.40.x` | Apple Git | 🟢 Active |
| **Platform** | `Darwin 27.2.0 (arm64)` | macOS Darwin Apple Silicon | Darwin Kernel | 🟢 Active |

---

## 🛠️ 1. CLI Tools & System Utilities

| Tool | Version / Status | Role & Purpose |
| :--- | :--- | :--- |
| **FFmpeg** | `ffmpeg version 9.0.2 Copyright (c) 2000-2026 the FFmpeg developers` | The decoding, the cutting of the video/audio, the conform of the timelines |
| **Tesseract OCR** | `tesseract 5.5.4` | The optical recognition of the text from the scans and the screenshots |
| **yt-dlp** | `2026.10.26` | The download of the media and the transcripts of the YouTube (`yt_analyze.py`) |
| **uv** | `uv 0.13.7 (Homebrew 2026-11-03 aarch64-apple-darwin)` | The ultra-fast manager of the packages and the virtual environments of the Python |
| **GitHub CLI (gh)** | `gh version 2.103.3 (2026-10-26)` | The control of the repositories, the PR and the releases of the GitHub |
| **jq** | `jq-1.8.2` | The streaming filtering and the parsing of the JSON in the terminal |
| **SQLite3** | `3.54.0 2026-04-09 12:25:13 8fa8248e303219400c646a885e36dfc52eae33d83f4412e3f369b2be5373aapl (64-bit)` | The embedded storage of the indexes and the tasks (`task_vault.db`) |
| **tmux** | `tmux 3.8` | The multiplexer of the terminal sessions |

---

## 🎨 2. DCC, 3D & Creative Suites (Muscle Realm)

| Software / Suite | Version / Status | Production Domain / Role |
| :--- | :--- | :--- |
| **Blender** | `Blender 5.1.1` | The 3D modeling, the procedural assets, the render (`cg_workspace`) |
| **Houdini** | `22.0.466` | The procedural FX/dynamics, the Solaris, the USD pipeline |
| **DaVinci Resolve** | `21.1.1` | The color grading, the final editing, the conform of the shots (`openmontage-builder`) |
| **Xcode** | `27.2` | The native development of the iOS/macOS games and the applications (the Island 9) |
| **Comfy Desktop** | `1.1.9` | The neural network generation and the stylization of the shots (ComfyUI / ControlNet) |
| **Unity Hub** | `NOT_INSTALLED` | The manager of the game engines of the Unity (Standby / Cross-platform) |

---

## 📱 3. Desktop Applications & System Bridges

| Application | Version / Status | System Interaction |
| :--- | :--- | :--- |
| **Obsidian** | `1.6.7` | The sovereign cognitive space (Brain Realm) |
| **Mattermost** | `6.3.2` | The corporate messenger of the studio of the Studio (`mattermost_sync.py`) |
| **Telegram** | `13.1.0` | The channels, the bots and the operational communication (`tg_bot_app`) |
| **Docker** | `4.99.0` | The containerization of the microservices and the databases |

---

### 📦 Installed Python Packages & Modules (56 total)

#### 🔹 Data & Document Processing

| Package / Module | Version | Architectural Role in AnD os |
| :--- | :--- | :--- |
| `docutils` | `0.22.4` | System utility |
| `Jinja2` | `3.1.6` | System utility |
| `markdown-it-py` | `4.2.0` | Markdown document parsing and processing |
| `MarkupSafe` | `3.0.3` | System utility |
| `numpy` | `2.5.1` | Numerical mathematics and scientific array computation |
| `openpyxl` | `3.1.5` | Excel workbook calculation and analysis (budgets, schedules) |
| `pdfminer.six` | `20260107` | PDF parsing and text twin extraction (MarkItDown engine) |
| `pdfplumber` | `0.11.10` | PDF parsing and text twin extraction (MarkItDown engine) |
| `pillow` | `12.2.0` | Image and asset texture validation/processing |
| `pypdfium2` | `5.10.1` | PDF parsing and text twin extraction (MarkItDown engine) |
| `rich` | `15.0.0` | Terminal formatting and CLI syntax highlighting |

#### 🔹 Network, API & Integration

| Package / Module | Version | Architectural Role in AnD os |
| :--- | :--- | :--- |
| `curl_cffi` | `0.15.0` | System utility |
| `ftrack-python-api` | `3.1.0` | Ftrack Studio API integration (Mars & Kot Gantt engines) |
| `telemetry_syncconnect` | `0.3.8` | telemetry_sync biometric and athletic performance synchronization |
| `requests` | `2.34.2` | HTTP client for system APIs and gateway connections |
| `ua-generator` | `2.1.2` | System utility |
| `urllib3` | `2.7.0` | System utility |
| `websocket-client` | `0.59.0` | System utility |
| `youtube-transcript-api` | `1.2.4` | YouTube transcript and summary extraction |

#### 🔹 Security, Crypto & System

| Package / Module | Version | Architectural Role in AnD os |
| :--- | :--- | :--- |
| `certifi` | `2026.7.22` | System utility |
| `cffi` | `2.0.0` | System utility |
| `cryptography` | `49.0.0` | Cryptographic primitives and secret key protection |
| `defusedxml` | `0.7.1` | System utility |
| `platformdirs` | `4.11.0` | System utility |
| `pycparser` | `3.0` | System utility |

#### 🔹 Build & Core Infrastructure

| Package / Module | Version | Architectural Role in AnD os |
| :--- | :--- | :--- |
| `packaging` | `26.2` | System utility |
| `pip` | `26.1.2` | System utility |
| `pybind11` | `3.0.4` | System utility |
| `Pygments` | `2.20.0` | System utility |
| `Sphinx` | `9.1.0` | System utility |
| `wheel` | `0.47.0` | System utility |

#### 🔹 Other Utilities

| Package / Module | Version | Architectural Role in AnD os |
| :--- | :--- | :--- |
| `alabaster` | `1.0.0` | System utility |
| `arrow` | `0.17.0` | System utility |
| `babel` | `2.18.0` | System utility |
| `charset-normalizer` | `3.4.7` | System utility |
| `clique` | `1.6.1` | System utility |
| `et_xmlfile` | `2.0.0` | System utility |
| `idna` | `3.18` | System utility |
| `imagesize` | `2.0.0` | System utility |
| `iniconfig` | `2.3.1` | System utility |
| `mdurl` | `0.1.2` | System utility |
| `pluggy` | `1.7.0` | System utility |
| `pyparsing` | `2.4.7` | System utility |
| `pytest` | `9.2.0` | System utility |
| `python-dateutil` | `2.9.0.post0` | System utility |
| `PyYAML` | `6.0.3` | System utility |
| `roman-numerals` | `4.1.0` | System utility |
| `six` | `1.17.0` | System utility |
| `snowballstemmer` | `3.1.1` | System utility |
| `sphinx-notfound-page` | `1.1.0` | System utility |
| `sphinxcontrib-applehelp` | `2.0.0` | System utility |
| `sphinxcontrib-devhelp` | `2.0.0` | System utility |
| `sphinxcontrib-htmlhelp` | `2.1.0` | System utility |
| `sphinxcontrib-jsmath` | `1.0.1` | System utility |
| `sphinxcontrib-qthelp` | `2.0.0` | System utility |
| `sphinxcontrib-serializinghtml` | `2.0.0` | System utility |

---

## ⚡ 4. Core Executable Scripts (and_os/bin/ & sbin/ — 113 scripts)

| Script | Purpose & Description |
| :--- | :--- |
| `agent_handoff.py` | agent_handoff.py - Validator and Generator for AnD os Subagent Handoff Protocol. Ensures zero-context loss during inter-agent transitions co |
| `api_contract_generator.py` | api_contract_generator.py — Typed API & Microkernel Contract Generator AnD os v1.0.0 — System Engineering Layer (Type-Safe Contracts & Schemas |
| `app_bridge.py` | app_bridge.py — Dispatcher for seamless interaction between Obsidian and External Projects (v1.0.0). Manages project registration, health va |
| `app_deconstructor.py` | app_deconstructor.py — Automated Application & Service Architecture Deconstructor AnD os v1.0.0 — System Engineering Layer (Clean Architecture |
| `app_quick_check.py` | Python CLI Automation Script |
| `architect_engine.py` | architect_engine.py — Sovereign System Architecture & Project Scaffolding Engine. Master Systems Architect Module (Island 8 / Island 6). Imp |
| `artifact_capture.py` | artifact_capture.py - Visual Artifact & Diagnostic State Capture Engine on Failure. Captures: 1. macOS desktop/window screenshot via /usr/sb |
| `asset_indexer.py` | Asset Indexer for ANDREY OS (v1.0.0) Scans non-MD assets (images, archives, audio, binaries, code exports), maps them to parent context file |
| `audit_graph_orphans.py` | audit_graph_orphans.py — Precise graph-connectivity scanner of the Obsidian Vault. Finds files that appear as orphans in the Obsidian visual |
| `audit_tags_links.py` | audit_tags_links.py — check and delivery of catalog tags and CONTEXT navigation links. Principle: Think in Code (Rule #16) and Rule #1 (chec |
| `backup_engine.py` | backup_engine.py — Enterprise Backup Engine for AnD os v1.0.0. Features: - 100% Full Obsidian Vault backup (All knowledge domains, configs, co |
| `board_parser.py` | Board Parser & Visual Semantic Extractor (Miro, Holst, FigJam, Schemas) AnD os v1.0.0 - Think in Code Infrastructure Supports: 1. Visual parsi |
| `bootstrap_system.py` | bootstrap_system.py — Zero-Touch System Bootstrap & Platform Provisioning Engine. AnD os v1.0.0 (Rule №48: Zero-Cost Cross-Platform Unix Compa |
| `budget_calc.py` | budget_calc.py — Unified CLI module for budget and estimate computation (Think in Code / IPC Bus). Principle: Zero-Token Computation. Rate,  |
| `build_native.py` | build_native.py — System compiler of Python projects into native binaries (Rule #32). Supported compilers: - PyInstaller (primary) - Nuitka  |
| `build_resolver.py` | build_resolver.py — Autonomous build-error resolver with minimal diffs (Minimal Diffs). AnD os v1.0.0 — Island 8 (Kernel & Compiler) <-> Islan |
| `career_radar.py` | career_radar.py — Executive Market Radar & Opportunity Matcher Part of AnD os | Rule #16 (Think-in-Code), Rule #54 (Zero-Orphans), Rule #59  |
| `cg_bridge.py` | CG Pipeline Integration Bridge (cg_bridge.py) AnD os v1.0.0 - Think in Code Infrastructure Provides a reliable, token-efficient and reproducib |
| `checkpoint_manager.py` | checkpoint_manager.py - High-Performance APFS CoW & Git State Checkpoint Engine for AnD os. Combines Apple File System instantaneous copy-on |
| `clean_links.py` | clean_links.py — safe normalization of links to missing images. Proxy-shim to the monolithic and_os.lib.vault library. |
| `closed_loop.py` | closed_loop.py — The Unified Master Dispatcher of the Closed Loop (Closed-Loop Sovereign OS Stack v1.0). Provides the end-to-end registratio |
| `codemap_engine.py` | codemap_engine.py — Ultra-lightweight architectural code map generator (Codemaps Engine). AnD os v1.0.0 — Island 8 (Kernel & System Compiler). |
| `comfy_graph.py` | comfy_graph.py — ComfyUI Graph Analysis, Validation, Visualization, and Sync Engine (Think in Code). Supported Formats: 1. Web UI Workflow J |
| `comfy_node_registry.py` | comfy_node_registry.py — Active ComfyUI Node Version Registry & Validator (Rule #45 & Update Guard). Principles: Think in Code (Rule #16), 1 |
| `context_budget_guard.py` | context_budget_guard.py — Context budget guard and phase compactor for AnD os v1.0.0. Island 8 (Kernel Core) <-> the agent's instrumental runt |
| `context_bundler.py` | Task Context Bundler & Output Trimming Utility AnD os v1.0.0 - Think in Code Context Squeezer Collects minimum sufficient context for tasks (s |
| `context_mode_manager.py` | context_mode_manager.py - Context Mode Switcher for AnD os v1.0.0. Manages active behavioral presets (dev, research, review) for LLM agents. |
| `context_router.py` | context_router.py — The smart quick DB and the router of the contextual files of the ANDREY OS (v1.0.0). Indexes all the CONTEXT.md in the V |
| `continuous_learner.py` | continuous_learner.py — Intelligent experience compiler of sessions for AnD os v1.0.0. Island 8 (Kernel & Compiler) <-> Island 1 & 6 (Knowledg |
| `convert_doc.py` | convert_doc.py — The universal converter of the documents into the clean Markdown for the LLM on the base of the Microsoft MarkItDown with t |
| `dag_planner.py` | dag_planner.py - DAG Phase Planner & Acceptance Criteria Engine for AnD os. Enforces Rule #20 and Rule #36 (Atomic Phased Execution & DoD Ch |
| `dash_smoke_test.py` | dash_smoke_test.py — Headless Smoke-Tester for Dash / Plotly web applications (Mars, Kot, Dino, etc.). Checks: 1. The syntactic integrity of |
| `dependency_engine.py` | dependency_engine.py — Unified System Dependency Analyzer & Cascade Synchronizer. AnD os v1.0.0 (Pillar II & VI: Full Information Dependency & |
| `dev_flow.py` | dev_flow.py — Modular CLI orchestrator for strict step-by-step development in AnD os. Manages the development session via a deterministic FS |
| `doc_analyze.py` | doc_analyze.py — The universal analyzer of the documents, the tables, the PDF and the images. Implements the Think in Code principle (Rule # |
| `docs_sync.py` | docs_sync.py - Automatic Runbook and Documentation Synchronizer for AnD os v1.0.0. Parses SSOT configurations (system.json, sys_cli.py, root_c |
| `editorial_otio_conform.py` | editorial_otio_conform.py — OpenTimelineIO Editorial Conform Engine (AnD os v1.0.0) Conforms editorial timelines, handles EDL/XML/OTIO interch |
| `eval_engine.py` | eval_engine.py - Eval-Driven Development (EDD) Framework for AnD os. Inspired by Everything-Claude-Code eval harness and adapted for determi |
| `export_kernel.py` | export_kernel.py — Zero-Leak Deterministic Kernel Exporter for AnD os. Extracts and sanitizes only open-source microkernel components. Part  |
| `finance_bridge.py` | finance_bridge.py — Analytical and Synchronization Gateway of the Financial Capital (AnD os v1.0.0). Provides a 100% local, hermetic (Air-Gap) |
| `fix_webdav_sync_issues.py` | fix_webdav_sync_issues.py — The complex fix of the problematic paths and the files for the stable synchronization of the WebDAV: 1. The repl |
| `ftrack_cache.py` | Caching module for Ftrack API dumps: reduces token spend and speeds up analysis. Features: query_cached(session, query_str, cache_key, max_a |
| `ftrack_gantt_exporter.py` | ftrack_gantt_exporter.py — Pinpoint Ftrack data export module for the Gantt Chart (v2.0.0). Supports filtering by projects (--project mars / |
| `ftrack_inspector.py` | ftrack_inspector.py — Analyzer of the Ftrack structure and the staged careful data retrieval. Features: 1. inspect: the deep audit of the pr |
| `ftrack_report.py` | Ftrack -> tables -> the status report (Kot / Mars). Modes: python3 ftrack_report.py --project kot --export        # export the raw data into |
| `ftrack_sync.py` | Synchronization Ftrack -> Obsidian for the projects Kot Ucheny and Motomars PM. Uses the unified optimized analytical engine ftrack_report.  |
| `telemetry_sync_sync.py` | The extended synchronization telemetry_sync Connect -> Obsidian (health.md, telemetry_sync.md, sport.md). Extracts the exhaustive layer of the biometrics an |
| `gen_context.py` | Context generator for external LLMs (ChatGPT, Claude, Gemini). Collects all CONTEXT.md files from the Obsidian Vault into a single file, opt |
| `graph_builder.py` | graph_builder.py — Engine of the task graphs generation and orchestration (Execution DAG). Part of the Task Execution Graph standard (Rule # |
| `health_bridge.py` | health_bridge.py — Unified analytical and synchronization gateway of the ANDREY OS family health (AnD os v1.0.0). Standards: - Rule #7: Dual-c |
| `hybrid_animatic_director.py` | hybrid_animatic_director.py — AI-Assisted Storyboard & 3D Animatic Assembler AnD os v1.0.0 — Studio Production & Narrative Layer (Island 4 & I |
| `hybrid_comfyui_render.py` | hybrid_comfyui_render.py — Multi-Pass 3D-to-AI Styler and ComfyUI Dispatcher AnD os v1.0.0 — Hybrid Production Layer (Island 7 & 3D Pipeline)  |
| `image_ocr.py` | Image OCR analyzer via tesseract. Uses tesseract OCR with the rus+eng language packs. Install: brew install tesseract tesseract-lang Run: py |
| `language_migration.py` | language_migration.py — Rule #3 EN-migration workbench (audit R2, WI-5.3). Machine-readable backlog and progress tracking for the Cyrillic - |
| `link_graph_orphans.py` | link_graph_orphans.py — Idempotent attachment of isolated notes to the root and category hubs of Obsidian. Goal: 1. For each isolated note ( |
| `manifest_projector.py` | manifest_projector.py — Root Manifest Projector (Single Source of Truth Guard). The canonical system manifest lives at and_os/etc/system.jso |
| `mattermost_inspector.py` | mattermost_inspector.py — The analyzer of the structure, the auditor and the staged extractor of the Mattermost slices. The architectural st |
| `mattermost_sync.py` | Mattermost API -> the digest of the messages and the follow-ups (Studio). Modes: python3 mattermost_sync.py --teams                           |
| `mirror_collector.py` | mirror_collector.py — Deterministic Monthly Telemetry Aggregator for AnD os (Island 6). Aggregates factual metrics across: 1. Studio Product |
| `notify_macos.py` | notify_macos.py — Нативный мост уведомлений macOS Notification Center (без звука). Принципы: Think in Code (Правило №16), Silent Native Aler |
| `obsidian_blueprint_generator.py` | obsidian_blueprint_generator.py — Generator of the reference architecture and plugins passport of Obsidian. AnD os v1.0.0 — Production Environ |
| `passport_sync_runner.py` | passport_sync_runner.py — Daily cron wrapper for the Island 7 passport sync. Runs the library-level PulsarPassportSync (and_os/lib/pulsar/pa |
| `pdf_twin_converter.py` | pdf_twin_converter.py — Automatic creation of informational Markdown twins for PDFs. Principle: Think in Code (Rule #16), Data Safety (Rule  |
| `post_prompt_planner.py` | post_prompt_planner.py — Automatic generator of process maps (Post-Prompt Execution Map / DAG Planner). Principle: Think in Code (Rule #16), |
| `postmortem_analyzer.py` | postmortem_analyzer.py — Production Bottleneck & Sprint Postmortem Analyzer AnD os v1.0.0 — Studio Production Layer (Island 5: Studio & Theory  |
| `proc_mesh.py` | proc_mesh.py — Generation and reading of the virtual state space (/proc mesh). Principle: Think in Code (Rule #16), 0-Token State Reading, L |
| `project_manager.py` | project_manager.py — Universal Project & App Onboarding Dispatcher for AnD os v1.0.0. Automatically registers new projects in Nero/pulsar (Isl |
| `project_registry.py` | project_registry.py — Unified Registry of External Software Systems and Web Services, ANDREY OS (v1.0.0). Catalogs all autonomous external s |
| `project_skeleton.py` | project_skeleton.py — Reference project skeleton generator (Skeleton Engine). AnD os v1.0.0 — Island 9 (Xcode / iOS Game Engineering) & Island |
| `projects_registry_sync.py` | projects_registry_sync.py — External Project Registry Regenerator (SSoT sync). Regenerates and_os/srv/projects_registry.json from live sourc |
| `quick_find.py` | quick_find.py — Fast Knowledge Retrieval Tool with Okapi BM25 & Bilingual Expansion AnD os v1.0.0 — Think in Code Knowledge Retrieval Engine ( |
| `quick_verify.py` | quick_verify.py - Fast 6-Phase Pre-Flight Verification Loop for AnD os. Inspired by Everything-Claude-Code verification principles and adapt |
| `refactor_cleaner.py` | refactor_cleaner.py - Safe Refactoring and Dead Code Cleaner for AnD os v1.0.0. Analyzes Python & Swift ASTs for unused functions, dead code b |
| `register_component.py` | Component Lifecycle & Registration Engine (register_component.py) AnD os v1.0.0 - Modular Architecture Infrastructure The automated tool for t |
| `rules_compiler.py` | rules_compiler.py — Fast Rules Index Compiler for AnD os (v2, audit R2 P3). Compiles the canonical manifest (and_os/etc/system.json — SSoT)  |
| `rules_fulltext_expander.py` | rules_fulltext_expander.py — Canonical Rule Section Restorer & Consistency Guard. Restores missing "### Правило N:" sections in .opencode/ru |
| `run_tests.py` | run_tests.py — Canonical AnD os test-suite runner. Single entrypoint for `pytest and_os/tests` with the hermetic-FHS contract (Rule #50) enf |
| `safe_snapshot.py` | safe_snapshot.py — Management of system state snapshots (APFS Local Snapshot & State Snapshots). Principles: APFS Native CoW (Rule #42, #43) |
| `schema_validator.py` | schema_validator.py — IPC response schema validation engine for system modules (Pydantic / Schema Engine). Principle: Data Contract Validati |
| `script_bible_extractor.py` | script_bible_extractor.py — Narrative IP & Script Bible Entity Extractor AnD os v1.0.0 — Narrative & Creative Layer (Island 4: Story & Books)  |
| `script_chunker.py` | script_chunker.py — the tool of the smart extraction of the fragments from the large texts/scripts/books. The principle: Think in Code (Rule |
| `sec_audit.py` | sec_audit.py - Security Audit & OWASP Top-10 / Injection Scanner for AnD os. Performs AST and heuristic analysis on Python, Swift, Shell, an |
| `session_gate.py` | session_gate.py — Universal Session Gate & Domain Anchor Beacon. Acts as a SessionStart lifecycle hook for Antigravity & LLM agents. Injects |
| `skill_abi_backfill.py` | skill_abi_backfill.py — SKILL_MODULE_ABI frontmatter backfill (audit R2, WI-5.1). Adds the ABI-mandated `ttl` and `reviewed` keys to every S |
| `skill_bus.py` | skill_bus.py — Microkernel Skill Bus & Interop Engine (AnD os v1.0.0) Universal gateway for all 58 system skills: - inspect: zero-token archit |
| `skill_dormancy_checker.py` | Skill Usage & Dormancy Analyzer AnD os v1.0.0 - Skill Governance (Rule №18) Parses and_os/lib/skills/telemetry.md, matches against all registe |
| `sos_auditor.py` | sos_auditor.py — Skill Operating Stack (SOS) Parallel Multi-Core Auditor. High-speed parallel diagnostic engine for AnD os skills. Verifies  |
| `state_manager.py` | state_manager.py (v1.2.0) — Unified Domain State Manager (IPC Bus). Manages, persists, and reconciles lean JSON states across core domains:  |
| `statusline.py` | statusline.py — Dynamic kernel statusline (Runtime Statusline Beacon). AnD os v1.0.0 — Island 8 (Kernel & AND_Terminal :8099). Prints a compac |
| `sync_context.py` | sync_context.py — the automation of the synchronization of the CONTEXT.md in the Obsidian Vault. The principle: Think in Code (Rule #16). Us |
| `sync_preflight.py` | sync_preflight.py — Pre-flight scanner of changes and structure synchronizer of AnD os. Rule #47: Pre-Flight Context & Cross-Chat Delta Sync |
| `sync_service.py` | sync_service.py — High-speed session initialization service (Fast Session Init Service v2.0). Runs direct module imports in a single Python  |
| `sys_bus.py` | sys_bus.py — CLI Adapter for AnD os Canonical Event Journal. Part of AnD os System Binaries (and_os/bin/). Delegates 100% of journal writes  |
| `sys_cli.py` | sys_cli.py — Unified Modular Dispatcher of AnD os (Modular Core CLI). Consolidates all system scripts and core modules into a single CLI wit |
| `system_dashboard.py` | system_dashboard.py — The Autonomous Interactive TUI Dashboard (AnD os v1.0.0 Live Top). Principles: Think in Code (Rule #16), the Rich TUI (t |
| `system_tools_map.py` | system_tools_map.py — The Automatic Generator of the Unified System Passport of the Toolkit and the Runtimes (Toolchain & Runtime Engine). T |
| `task_db_engine.py` | task_db_engine.py — Local Task Database and Vault Indexing Engine (SQLite Engine). Principle: Think in Code (Rule #16), Zero-Token Querying. |
| `tasks_bridge.py` | tasks_bridge.py — Analytical and Synchronization Gateway of the Production Pulse (Tasks & Production Pulse). Provides token-efficient (<50 t |
| `tdd_scaffold.py` | tdd_scaffold.py - TDD Test Scaffold Generator for AnD os (Python & Swift). Extracts classes, functions, and methods from source files and ge |
| `telemetry_logger.py` | telemetry_logger.py — Fast telemetry logging module (IPC Bus). Modular program for appending validated records to and_os/lib/skills/telemetr |
| `temporal_consistency_guard.py` | temporal_consistency_guard.py — Frame Deflicker & Temporal Consistency Checker AnD os v1.0.0 — Quality & Animation Gate (Island 7 & Production |
| `tg_career_fetcher.py` | tg_career_fetcher.py — Hybrid Telegram Career Ingestion Engine. Part of career-radar ecosystem | Rule #56 (No Hallucinations) & Rule #16 (To |
| `trim_output.py` | trim_output.py — Sandbox CLI execution wrapper with automatic log truncation (Rule #24). Keeps Head (first N lines) + Tail (last M lines), f |
| `ui_inspector.py` | ui_inspector.py — High-efficiency inspector of GUI/Dash/HTML components (ANDREY OS). Allows, without loading hundreds of code lines into the |
| `vacuum_cleaner.py` | vacuum_cleaner.py — AnD os System Sanitizer & Junk Collector (v1.0.0). Cleans the Obsidian Vault and the Pulsar ecosystem from junk artifact |
| `validate_system.py` | validate_system.py — Modular master dispatcher of the self-diagnostics and audit of AnD os. Health Grid architecture (Ring 0 - Ring 4): - Ri |
| `vault_guard_hook.py` | vault_guard_hook.py — Hardware-Level PreToolUse Governance Hook. Implements Dual-Speed Governance (Rule #19 Invariant): - Fast-Track (Core,  |
| `vfs_bridge.py` | vfs_bridge.py — CLI Router and Bridge for VFS Subsystem in AnD os v1.0.0. Part of AnD os Binary Bridges (and_os/bin/). Commands: sys_cli.py vf |
| `video_harness.py` | video_harness.py — Autonomous technical QC validator for video and passes (Video E2E Harness). AnD os v1.0.0 — Island 7 & 5 (Pulsar & CG Produ |
| `video_scenes.py` | video_scenes.py — The selective media analysis of the video via the FFmpeg (Scene Detection). A part of the standard Think in Code (Rule #16 |
| `weeek_sync.py` | Weeek Sync — extraction and analytics of the tasks from Weeek (Studio). Works without an API key via direct reading of the open Safari tabs ( |
| `xl_analyze.py` | Excel/Google Sheets analyzer: reading formulas, links, structure. Run: python3 xl_analyze.py <path to file> [--sheet name] [--formulas] [--s |
| `yt_analyze.py` | YouTube video data extraction. python3 yt_analyze.py <url> --transcript  — transcript python3 yt_analyze.py <url> --info        — metadata p |

---

## 🧠 5. Declarative Skills (and_os/lib/skills/ — 67 skills)

| Skill | Purpose & Routing |
| :--- | :--- |
| `[[and_os/lib/skills/ai-rule/SKILL|ai-rule]]` | Use when creating, testing, or updating canonical 5-part system rules in .opencode/rules.md per the Rule #41 Governance Gate. |
| `[[and_os/lib/skills/api-contract-generator/SKILL|api-contract-generator]]` | Use when generating strict JSON schema contracts, TypeScript interfaces, and inter-process communication specs between services. |
| `[[and_os/lib/skills/app-bridge/SKILL|app-bridge]]` | Use when synchronizing shared state contracts, blueprints, and IPC data channels between Obsidian and Pulsar applications. |
| `[[and_os/lib/skills/app-deconstructor/SKILL|app-deconstructor]]` | Use when deconstructing foreign codebases into architectural blueprints, interfaces, subcommands, and dependency graphs. |
| `[[and_os/lib/skills/board-analyzer/SKILL|board-analyzer]]` | Use when parsing and analyzing visual boards (Canvas, Miro, FigJam) to extract cards, connections, and structured task graphs. |
| `[[and_os/lib/skills/book-hub/SKILL|book-hub]]` | Use when ingesting, structuring, and breaking down book notes into 8-block actionable summaries with practical frameworks. |
| `[[and_os/lib/skills/book-summary-practical/SKILL|book-summary-practical]]` | Use when transforming raw book reading notes into execution toolkits, management checklists, and pipeline threshold tables. |
| `[[and_os/lib/skills/budget-calculator/SKILL|budget-calculator]]` | Use when calculating studio shot production costs, render farm budgets, contractor payroll rates, and commercial project estimates. |
| `[[and_os/lib/skills/career-radar/SKILL|career-radar]]` | Use when executing weekly executive market intelligence scans, vacancy scoring, and career opportunity radar for System Architect across CG animation,  |
| `[[and_os/lib/skills/cg-article/SKILL|cg-article]]` | Use when drafting thought-leadership articles, case studies, and analytical breakdowns for CG_core social channels. |
| `[[and_os/lib/skills/cg-content-factory/SKILL|cg-content-factory]]` | Use when batch generating multimedia CG marketing assets, shot breakdowns, and multi-platform promotional content. |
| `[[and_os/lib/skills/cg-core-consulting/SKILL|cg-core-consulting]]` | Use when auditing animation studio pipelines, diagnosing production bottlenecks, or formulating B2B CG advisory curricula. |
| `[[and_os/lib/skills/cg-pipeline/SKILL|cg-pipeline]]` | Use when executing multi-DCC production pipeline steps: procedural modeling, scene assembly, USD overrides, and master cutting. |
| `[[and_os/lib/skills/clean-code-guardian/SKILL|clean-code-guardian]]` | Use when authoring, reviewing, or refactoring Python code to enforce Uncle Bob clean architecture, zero silent exceptions, and low nesting. |
| `[[and_os/lib/skills/clipping-finder/SKILL|clipping-finder]]` | Use when searching across raw clippings, web extracts, and unstructured articles in Clippings/ to extract core insights for active tasks. |
| `[[and_os/lib/skills/comfy-builder/SKILL|comfy-builder]]` | Use when designing, compiling, or refactoring JSON node graphs for ComfyUI desktop and standalone execution. |
| `[[and_os/lib/skills/context-compressor/SKILL|context-compressor]]` | Use when compressing large multi-file directories and codebase contexts into minimal-token Markdown bundles per Rule #44. |
| `[[and_os/lib/skills/decision-log/SKILL|decision-log]]` | Use when capturing and recording irreversible architectural, business, technology, or personal Architecture Decision Records (ADRs). |
| `[[and_os/lib/skills/dev-flow/SKILL|dev-flow]]` | Use when planning multi-step software engineering cycles, designing test coverage matrices, and managing git branches. |
| `[[and_os/lib/skills/document-hub/SKILL|document-hub]]` | Use when converting, extracting text, OCR parsing, or restructuring PDFs, DOCX, and spreadsheet documents. |
| `[[and_os/lib/skills/editorial-otio-conform/SKILL|editorial-otio-conform]]` | Use when cutting shot timelines, calculating frame handles, performing roundtrip conforms, and interchanging EDL/XML/OTIO files. |
| `[[and_os/lib/skills/employee-hub/SKILL|employee-hub]]` | Use when evaluating artist competency scorecards, aggregating crew feedback, and auditing workload across studio departments. |
| `[[and_os/lib/skills/endurance-training-plan/SKILL|endurance-training-plan]]` | Use when designing structured marathon, half-marathon, and cycling training blocks with heart rate and power zone periodization. |
| `[[and_os/lib/skills/executive-mirror/SKILL|executive-mirror]]` | Use when executing monthly 360° personal retrospectives, cross-island attention audits, and closed-loop strategic calibrations against the 20-year vis |
| `[[and_os/lib/skills/external-skills-gateway/SKILL|external-skills-gateway]]` | Use when searching, inspecting, filtering, or integrating open-source agent skills from skills.sh, Vercel Labs, and GitHub into AnD os. |
| `[[and_os/lib/skills/ftrack-sync/SKILL|ftrack-sync]]` | Use when synchronizing project milestones, shot progress, asset statuses, and task assignments from Ftrack API for Mars and Kot productions. |
| `[[and_os/lib/skills/telemetry_sync/SKILL|telemetry_sync]]` | Use when retrieving nocturnal HRV, sleep architecture, resting HR, and ACWR training load indices from telemetry_sync Connect. |
| `[[and_os/lib/skills/github-ops/SKILL|github-ops]]` | Use when searching GitHub repositories, inspecting issues, analyzing pull requests, checking CI/CD workflow runs, reading remote code, or tracking rel |
| `[[and_os/lib/skills/goal-writer/SKILL|goal-writer]]` | Use when formulating SMART annual, quarterly, and life milestone goals across career, health, creative, and family domains. |
| `[[and_os/lib/skills/health-diagnostics-hub/SKILL|health-diagnostics-hub]]` | Use when analyzing laboratory blood biomarkers, ultrasound findings, clinical consultation notes, and preventive health panels. |
| `[[and_os/lib/skills/health-orchestrator/SKILL|health-orchestrator]]` | Use when computing cross-domain clinical health synthesis, orthopedics vs running cadence, and athletic recovery clearances. |
| `[[and_os/lib/skills/higgsfield-seedance-prompt/SKILL|higgsfield-seedance-prompt]]` | Use when engineering cinematic camera movement, lighting, and temporal coherence prompts for Higgsfield and Seedance video models. |
| `[[and_os/lib/skills/hybrid-animatic-director/SKILL|hybrid-animatic-director]]` | Use when directing hybrid 2D/3D/AI animatics, synthesizing shot transitions, and planning camera keyframe layouts. |
| `[[and_os/lib/skills/hybrid-comfyui-render/SKILL|hybrid-comfyui-render]]` | Use when batch executing 3D neural passes, depth maps, and latent upscaling via local ComfyUI workers. |
| `[[and_os/lib/skills/investor-outreach/SKILL|investor-outreach]]` | Use when composing personalized investor pitches, grant applications (IRI, ON Media), and follow-up investment communications. |
| `[[and_os/lib/skills/ios-game-builder/SKILL|ios-game-builder]]` | Use when prototyping, engineering, compiling, and debugging native iOS/macOS games and apps in Swift, SwiftUI, and SpriteKit without user programming. |
| `[[and_os/lib/skills/knowledge-promoter/SKILL|knowledge-promoter]]` | Use when orchestrating closed-loop memory in AnD os: running Pre-flight Recall to retrieve negative constraints before execution, or Post-flight Learn |
| `[[and_os/lib/skills/llm-council/SKILL|llm-council]]` | Use when orchestrating multi-agent consensus debates, adversarial evaluations, and multi-model synthesis on critical decisions. |
| `[[and_os/lib/skills/mattermost-sync/SKILL|mattermost-sync]]` | Use when synchronizing studio chat channels, compiling daily communication digests, and isolating cross-departmental blockers. |
| `[[and_os/lib/skills/meetings-hub/SKILL|meetings-hub]]` | Use when decomposing production meeting transcripts into prioritized action points with assignees and deadline milestones. |
| `[[and_os/lib/skills/negotiation/SKILL|negotiation]]` | Use when preparing for high-stakes business negotiations, difficult team conversations, client pitches, or contractual objections. |
| `[[and_os/lib/skills/obsidian-bases/SKILL|obsidian-bases]]` | Use when creating, validating, and maintaining Obsidian Bases (.base files) with views, reactive filters, formulas, and summaries for database-like ta |
| `[[and_os/lib/skills/openmontage-builder/SKILL|openmontage-builder]]` | Use when performing generative video assembly, timeline orchestration, reference-guided pacing cuts, and automated hardware-accelerated FFmpeg editing |
| `[[and_os/lib/skills/portfolio-summary/SKILL|portfolio-summary]]` | Use when analyzing personal multi-currency financial balances, investment brokerage assets, and monthly cashflow dynamics. |
| `[[and_os/lib/skills/postmortem-analyzer/SKILL|postmortem-analyzer]]` | Use when conducting sprint postmortems, isolating production bottlenecks via Theory of Constraints (TOC), and updating lessons learned. |
| `[[and_os/lib/skills/project-state/SKILL|project-state]]` | Use when capturing operational delta snapshots of active studio production projects, sprint velocity, and blocker states. |
| `[[and_os/lib/skills/prompt-improver/SKILL|prompt-improver]]` | Use when refining agent system prompts, clarifying underspecified user queries, and distilling high-fidelity context instructions. |
| `[[and_os/lib/skills/reverse-engineer-anything/SKILL|reverse-engineer-anything]]` | Reverse engineer native, managed, Electron/JavaScript, packaged, firmware, SQLite, and browser targets with REA. Use shipped-artifact or requested run |
| `[[and_os/lib/skills/script-bible-extractor/SKILL|script-bible-extractor]]` | Use when distilling narrative bibles, character rosters, location indices, and lore continuity from screenplays and novels. |
| `[[and_os/lib/skills/skill-creator/SKILL|skill-creator]]` | Use when creating, validating, linting, or updating skills in AnD os. Enforces SKILL_MODULE_ABI v2.1, 8-Island architectural binding, clean code stand |
| `[[and_os/lib/skills/skill-router/SKILL|skill-router]]` | Use when arbitrating between competing domain skills and routing complex multi-step user prompts to the single primary skill. |
| `[[and_os/lib/skills/status-report/SKILL|status-report]]` | Use when compiling executive producer status reports for Mars and Kot animation features with department velocity and dependencies. |
| `[[and_os/lib/skills/story-dev/SKILL|story-dev]]` | Use when developing dramaturgical animation narratives, character arcs, loglines, synopses, worldbuilding rules, or step outlines. |
| `[[and_os/lib/skills/strategy-review/SKILL|strategy-review]]` | Use when evaluating quarterly personal OKRs, strategic career development vectors, and multi-year life vision alignment. |
| `[[and_os/lib/skills/sync-context/SKILL|sync-context]]` | Use when updating CONTEXT.md maps upon filesystem file additions or edits, validating tag indexes, and repairing wikilinks. |
| `[[and_os/lib/skills/system-architect/SKILL|system-architect]]` | Use when bootstrapping new software projects, web services, games, 3D pipelines, or core modules. Enforces Spec-Before-Code, C4/ADR design docs, and r |
| `[[and_os/lib/skills/system-audit/SKILL|system-audit]]` | Use when running full 5-ring Health Grid integrity validations across filesystem syntax, knowledge graph, AST, and background daemons. |
| `[[and_os/lib/skills/ta-bu-plan/SKILL|ta-bu-plan]]` | Use when reviewing or expanding Ta-Bu animation startup strategy, unit economics, corporate legal structures, and domain roadmaps. |
| `[[and_os/lib/skills/task-graph/SKILL|task-graph]]` | Use when querying the SQLite task index, managing priority blockers, and computing dependency DAGs across all vault markdown TODOs. |
| `[[and_os/lib/skills/tax-compliance/SKILL|tax-compliance]]` | Use when calculating individual entrepreneur (IP) taxes, self-employed declarations, social fund payments, and accounting records. |
| `[[and_os/lib/skills/teach-hub/SKILL|teach-hub]]` | Use when constructing interactive pedagogical learning paths, mentoring trajectories, and mission-based curricula. |
| `[[and_os/lib/skills/temporal-consistency-guard/SKILL|temporal-consistency-guard]]` | Use when verifying visual and narrative continuity, character wardrobe constancy, and lighting consistency across AI video shots. |
| `[[and_os/lib/skills/uc-diet-planning/SKILL|uc-diet-planning]]` | Use when structuring medical nutrition protocols, gut-soothing weekly menus, and anti-inflammatory diets for chronic_condition (UC). |
| `[[and_os/lib/skills/ui-inspector/SKILL|ui-inspector]]` | Use when inspecting frontend web UI applications, probing HTTP ports for 200 OK liveness, and verifying stylesheet assets. |
| `[[and_os/lib/skills/vault-router/SKILL|vault-router]]` | Use when classifying and routing newly drafted notes, reports, and knowledge assets to their canonical Obsidian Vault folders. |
| `[[and_os/lib/skills/weeek-hub/SKILL|weeek-hub]]` | Use when synchronizing Weeek project workspaces, identifying overdue task blockers, or balancing sprint kanban boards. |
| `[[and_os/lib/skills/yt-analyze/SKILL|yt-analyze]]` | Use when parsing YouTube video transcripts, extracting visual keyframe timestamps, and compiling technical teardowns. |

---
[[SYSTEM_MAP|← Master Atlas SYSTEM_MAP.md]] | [[SYSTEM|← Master Manifest SYSTEM.md]]
