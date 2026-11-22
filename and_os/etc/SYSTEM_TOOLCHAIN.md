---
tags:
  - system
  - toolchain
  - context
  - runtime
created: 2026-11-22 16:30:18
---

# 🛠️ SYSTEM TOOLCHAIN — Runtime Standard & Toolchain Specification AnD os v1.2.0

> **Specification for AI Agents and Developers:** Canonical specification of programming language versions, installed libraries, 120 core scripts, and 51 active skills.  
> **Automated Refresh:** `python3 and_os/bin/sys_cli.py env` or `python3 and_os/bin/system_tools_map.py --build`

---

## ⚙️ 0. Runtime Environment Standard

| Language / Runtime | Current Version | Target Standard | Executable Path | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Python** | `3.12.11` | `>=3.11 (Recommended 3.14.x)` | `./and_os/.venv/bin/python3` | 🟢 Active |
| **Node.js** | `v26.13.1` | `>=20.x LTS` | `Node Runtime (Homebrew)` | 🟢 Active |
| **Deno** | `deno 2.9.8 (stable, release, aarch64-apple-darwin)` | Modern TS/JS Runtime | `Deno (Homebrew)` | 🟢 Active |
| **Go** | `go version go1.27.4 darwin/arm64` | Compiled Backend Runtime | `Go (Homebrew)` | 🟢 Active |
| **Swift** | `Apple Swift version 6.4 (swiftlang-6.4.0.34.1 clang-2100.3.34.1)` | Native Apple Ecosystem | `Apple Swift 6 Toolchain` | 🟢 Active |
| **Git** | `git version 2.54.0 (Apple Git-157)` | `>= 2.40.x` | Apple Git | 🟢 Active |
| **OpenCode** | `opencode v2.3.2` | The agent harness of the AnD os (the bun runner, the MCP mesh) | OpenCode CLI | 🟢 Active |
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
| **obsidian-cli** | `obsidian-cli version v0.2.3` | The command-line bridge to the Obsidian vault (the core-app interaction) |
| **xcodegen** | `Version: 2.46.0` | The generation of the Xcode project files (the Island 9) |
| **gemini-cli** | `0.68.0` | The Google LLM terminal agent |

---

## 🎨 2. DCC, 3D & Creative Suites (Muscle Realm)

| Software / Suite | Version / Status | Production Domain / Role |
| :--- | :--- | :--- |
| **Blender** | `Blender 5.1.1` | The 3D modeling, the procedural assets, the render (`cg_workspace`) |
| **Houdini** | `22.0.466` | The procedural FX/dynamics, the Solaris, the USD pipeline |
| **DaVinci Resolve** | `21.1.1` | The color grading, the final editing, the conform of the shots (`openmontage-builder`) |
| **Xcode** | `27.2` | The native development of the iOS/macOS games and the applications (the Island 9) |
| **Comfy Desktop** | `1.1.10` | The neural network generation and the stylization of the shots (ComfyUI / ControlNet) |
| **Unity Hub** | `NOT_INSTALLED` | The manager of the game engines of the Unity (Standby / Cross-platform) |

---

## 📱 3. Desktop Applications & System Bridges

| Application | Version / Status | System Interaction |
| :--- | :--- | :--- |
| **Obsidian** | `1.15.1` | The sovereign cognitive space (Brain Realm) |
| **Mattermost** | `6.4.0` | The corporate messenger of the studio of the Studio (`mattermost_sync.py`) |
| **Telegram** | `13.1.0` | The channels, the bots and the operational communication (`tg_bot_app`) |
| **Docker** | `4.99.0` | The containerization of the microservices and the databases |
| **Obsidian Web Clipper** | `1.7.1` | The web capture of the articles into the Clippings island |
| **Claude** | `6.6395.1` | The Anthropic LLM client (the tool_home is ~/.claude, the Claude Code CLI) |
| **Gemini** | `1.147.5.1526` | The Google LLM client (the tool_home is ~/.gemini, the gemini-cli) |
| **Zoom** | `6.6.10 (69071)` | The video calls and the production reviews |
| **Craft Anything** | `0.6.1` | The Craft note-taking suite (the *Craft components, the vendor is to confirm) |

---

### 📦 Installed Python Packages & Modules (85 total)

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
| `annotated-types` | `0.8.0` | System utility |
| `anyio` | `4.16.0` | System utility |
| `arrow` | `0.17.0` | System utility |
| `attrs` | `26.1.0` | System utility |
| `babel` | `2.18.0` | System utility |
| `charset-normalizer` | `3.4.7` | System utility |
| `click` | `8.5.1` | System utility |
| `clique` | `1.6.1` | System utility |
| `et_xmlfile` | `2.0.0` | System utility |
| `fxhoudinimcp` | `2.30.0` | System utility |
| `h11` | `0.16.0` | System utility |
| `httpcore` | `1.0.9` | System utility |
| `httpcore2` | `2.16.2` | System utility |
| `httpx` | `0.28.1` | System utility |
| `httpx2` | `2.16.2` | System utility |
| `idna` | `3.18` | System utility |
| `imagesize` | `2.0.0` | System utility |
| `iniconfig` | `2.3.1` | System utility |
| `jsonschema` | `4.26.0` | System utility |
| `jsonschema-specifications` | `2025.9.1` | System utility |
| `mcp` | `2.3.0` | System utility |
| `mcp-types` | `2.3.0` | System utility |
| `mdurl` | `0.1.2` | System utility |
| `opentelemetry-api` | `1.45.2` | System utility |
| `pluggy` | `1.7.0` | System utility |
| `pydantic` | `2.14.4` | System utility |
| `pydantic` | `2.14.3` | System utility |
| `pydantic_core` | `2.50.5` | System utility |
| `pydantic_core` | `2.50.4` | System utility |
| `PyJWT` | `2.15.1` | System utility |
| `pyparsing` | `2.4.7` | System utility |
| `pytest` | `9.2.0` | System utility |
| `python-dateutil` | `2.9.0.post0` | System utility |
| `python-multipart` | `0.0.34` | System utility |
| `PyYAML` | `6.0.3` | System utility |
| `referencing` | `0.37.0` | System utility |
| `roman-numerals` | `4.1.0` | System utility |
| `rpds-py` | `2026.9.1` | System utility |
| `six` | `1.17.0` | System utility |
| `snowballstemmer` | `3.1.1` | System utility |
| `sphinx-notfound-page` | `1.1.0` | System utility |
| `sphinxcontrib-applehelp` | `2.0.0` | System utility |
| `sphinxcontrib-devhelp` | `2.0.0` | System utility |
| `sphinxcontrib-htmlhelp` | `2.1.0` | System utility |
| `sphinxcontrib-jsmath` | `1.0.1` | System utility |
| `sphinxcontrib-qthelp` | `2.0.0` | System utility |
| `sphinxcontrib-serializinghtml` | `2.0.0` | System utility |
| `sse-starlette` | `3.7.0` | System utility |
| `starlette` | `1.10.0` | System utility |
| `truststore` | `0.10.5` | System utility |
| `typing-inspection` | `0.4.5` | System utility |
| `typing_extensions` | `4.16.0` | System utility |
| `uvicorn` | `0.54.0` | System utility |

---

## ⚡ 4. Core Executable Scripts (and_os/bin/ & sbin/ — 120 scripts)

| Script | Purpose & Description |
| :--- | :--- |
| `agent_handoff.py` | agent_handoff.py - Validator and Generator for AnD os Subagent Handoff Protocol. Ensures zero-context loss during inter-agent transitions co |
| `api_contract_generator.py` | api_contract_generator.py — Typed API & Microkernel Contract Generator AnD os v1.2.0 — System Engineering Layer (Type-Safe Contracts & Schem |
| `app_bridge.py` | app_bridge.py — Dispatcher for seamless interaction between Obsidian and External Projects (v1.1.0). Manages project registration, health va |
| `app_deconstructor.py` | app_deconstructor.py — Automated Application & Service Architecture Deconstructor AnD os — System Engineering Layer (Clean Architecture & Re |
| `app_quick_check.py` | Python CLI Automation Script |
| `architect_engine.py` | architect_engine.py — Sovereign System Architecture & Project Scaffolding Engine. Master Systems Architect Module (Island 8 / Island 6). Imp |
| `artifact_capture.py` | artifact_capture.py - Visual Artifact & Diagnostic State Capture Engine on Failure. Captures: 1. macOS desktop/window screenshot via /usr/sb |
| `asset_indexer.py` | Asset Indexer for ANDREY OS (v1.1.0) Scans non-MD assets (images, archives, audio, binaries, code exports), maps them to parent context file |
| `audit_graph_orphans.py` | audit_graph_orphans.py — Precise graph-connectivity scanner of the Obsidian Vault. Finds files that appear as orphans in the Obsidian visual |
| `audit_tags_links.py` | audit_tags_links.py — check and delivery of catalog tags and CONTEXT navigation links. Principle: Think in Code (Rule #16) and Rule #1 (chec |
| `backup_engine.py` | backup_engine.py — Enterprise Backup Engine for AnD os v1.2.0. Features: - 100% Full Obsidian Vault backup (All knowledge domains, configs,  |
| `board_parser.py` | Board Parser & Visual Semantic Extractor (Miro, Holst, FigJam, Schemas) AnD os v1.2.0 - Think in Code Infrastructure Supports: 1. Visual par |
| `bootstrap_system.py` | bootstrap_system.py — Zero-Touch System Bootstrap & Platform Provisioning Engine. AnD os v1.2.0 (Rule №48: Zero-Cost Cross-Platform Unix Com |
| `budget_calc.py` | budget_calc.py — Unified CLI module for budget and estimate computation (Think in Code / IPC Bus). Principle: Zero-Token Computation. Rate,  |
| `build_native.py` | build_native.py — System compiler of Python projects into native binaries (Rule #32). Supported compilers: - PyInstaller (primary) - Nuitka  |
| `build_resolver.py` | build_resolver.py — Autonomous build-error resolver with minimal diffs (Minimal Diffs). AnD os v1.2.0 — Island 8 (Kernel & Compiler) <-> Isl |
| `career_radar.py` | career_radar.py — Multi-Contour Executive & Opportunity Market Radar. Part of AnD os | Rule #16 (Think-in-Code), Rule #51 (Decoupling), Rule |
| `cg_bridge.py` | CG Pipeline Integration Bridge (cg_bridge.py) AnD os v1.2.0 - Think in Code Infrastructure Provides a reliable, token-efficient and reproduc |
| `checkpoint_manager.py` | checkpoint_manager.py - High-Performance APFS CoW & Git State Checkpoint Engine for AnD os. Combines Apple File System instantaneous copy-on |
| `clean_links.py` | clean_links.py — safe normalization of links to missing images. Proxy-shim to the monolithic and_os.lib.vault library. |
| `closed_loop.py` | closed_loop.py — The Unified Master Dispatcher of the Closed Loop (Closed-Loop Sovereign OS Stack v1.0). Provides the end-to-end registratio |
| `codemap_engine.py` | codemap_engine.py — Ultra-lightweight architectural code map generator (Codemaps Engine). AnD os v1.2.0 — Island 8 (Kernel & System Compiler |
| `comfy_graph.py` | comfy_graph.py — ComfyUI Graph Analysis, Validation, Visualization, and Sync Engine (Think in Code). Supported Formats: 1. Web UI Workflow J |
| `comfy_node_registry.py` | comfy_node_registry.py — Active ComfyUI Node Version Registry & Validator (Rule #45 & Update Guard). Principles: Think in Code (Rule #16), 1 |
| `context_budget_guard.py` | context_budget_guard.py — Context budget guard and phase compactor for AnD os v1.2.0. Island 8 (Kernel Core) <-> the agent's instrumental ru |
| `context_bundler.py` | Task Context Bundler & Output Trimming Utility AnD os v1.2.0 - Think in Code Context Squeezer Collects minimum sufficient context for tasks  |
| `context_mode_manager.py` | context_mode_manager.py - Context Mode Switcher for AnD os v1.2.0. Manages active behavioral presets (dev, research, review) for LLM agents. |
| `context_router.py` | context_router.py — The smart quick DB and the router of the contextual files of the ANDREY OS (v1.1.0). Indexes all the CONTEXT.md in the V |
| `continuous_learner.py` | continuous_learner.py — Intelligent experience compiler of sessions for AnD os v1.2.0. Island 8 (Kernel & Compiler) <-> Island 1 & 6 (Knowle |
| `convert_doc.py` | convert_doc.py — The universal converter of the documents into the clean Markdown for the LLM on the base of the Microsoft MarkItDown with t |
| `dag_planner.py` | dag_planner.py - DAG Phase Planner & Acceptance Criteria Engine for AnD os. Enforces Rule #20 and Rule #36 (Atomic Phased Execution & DoD Ch |
| `dash_smoke_test.py` | dash_smoke_test.py — Headless Smoke-Tester for Dash / Plotly web applications (Mars, Kot, Dino, etc.). Checks: 1. The syntactic integrity of |
| `dependency_engine.py` | dependency_engine.py — Unified System Dependency Analyzer & Cascade Synchronizer. AnD os v1.2.0 (Pillar II & VI: Full Information Dependency |
| `dev_flow.py` | dev_flow.py — Modular CLI orchestrator for strict step-by-step development in AnD os. Manages the development session via a deterministic FS |
| `doc_analyze.py` | doc_analyze.py — The universal analyzer of the documents, the tables, the PDF and the images. Implements the Think in Code principle (Rule # |
| `docs_sync.py` | docs_sync.py - Automatic Runbook and Documentation Synchronizer for AnD os v1.2.0. Parses SSOT configurations (system.json, sys_cli.py, root |
| `editorial_otio_conform.py` | editorial_otio_conform.py — OpenTimelineIO Editorial Conform Engine (AnD os v1.2.0) Conforms editorial timelines, handles EDL/XML/OTIO inter |
| `eval_engine.py` | eval_engine.py - Eval-Driven Development (EDD) Framework for AnD os. Inspired by Everything-Claude-Code eval harness and adapted for determi |
| `export_kernel.py` | export_kernel.py — Zero-Leak Deterministic Kernel Exporter for AnD os. Extracts and sanitizes only open-source microkernel components. Part  |
| `export_skills.py` | export_skills.py — Zero-Leak Autonomous Skills Exporter. Extracts standalone, portable AI skills for Claude Code, Cursor, OpenCode, and Gemi |
| `finance_bridge.py` | finance_bridge.py — Analytical and Synchronization Gateway of the Financial Capital (AnD os v1.2.0). Provides a 100% local, hermetic (Air-Ga |
| `fix_webdav_sync_issues.py` | fix_webdav_sync_issues.py — The complex fix of the problematic paths and the files for the stable synchronization of the WebDAV: 1. The repl |
| `fs_guard.py` | fs_guard.py -- Canonical Filesystem Map Guard (decision engine). Single, stateless decision engine behind the canonical FS map (SSoT data: a |
| `ftrack_cache.py` | ftrack_cache.py - Thin facade delegating to the canonical hub module. Audit R4, P3 (R4-DUP-1): the ftrack/mattermost/OCR stack lived in two  |
| `ftrack_daily_pipeline.py` | ftrack_daily_pipeline.py — the daily Ftrack read-only loop (22.11). 22.11 (Phase 3 closeout, Andrei decision, option A): the 07:30 ftrack_ca |
| `ftrack_gantt_exporter.py` | ftrack_gantt_exporter.py - Thin facade delegating to the canonical hub module. Audit R4, P3 (R4-DUP-1): the ftrack/mattermost/OCR stack live |
| `ftrack_inspector.py` | ftrack_inspector.py - Thin facade delegating to the canonical hub module. Audit R4, P3 (R4-DUP-1): the ftrack/mattermost/OCR stack lived in  |
| `ftrack_report.py` | ftrack_report.py - Thin facade delegating to the canonical hub module. Audit R4, P3 (R4-DUP-1): the ftrack/mattermost/OCR stack lived in two |
| `ftrack_sync.py` | ftrack_sync.py - Thin facade delegating to the canonical hub module. Audit R4, P3 (R4-DUP-1): the ftrack/mattermost/OCR stack lived in two l |
| `telemetry_sync_sync.py` | The extended synchronization telemetry_sync Connect -> Obsidian (health.md, telemetry_sync.md, sport.md). Extracts the exhaustive layer of the biometrics an |
| `gen_context.py` | Context generator for external LLMs (ChatGPT, Claude, Gemini). Collects all CONTEXT.md files from the Obsidian Vault into a single file, opt |
| `graph_builder.py` | graph_builder.py — Engine of the task graphs generation and orchestration (Execution DAG). Part of the Task Execution Graph standard (Rule # |
| `health_bridge.py` | health_bridge.py — Unified analytical and synchronization gateway of the ANDREY OS family health (AnD os v1.2.0). Standards: - Rule #7: Dual |
| `houdini_bridge.py` | Houdini bridge facade (external composition; kernel sys_cli.py untouched, Rule #15). Commands (Rule #73 execution protocol): status [--json] |
| `hybrid_animatic_director.py` | hybrid_animatic_director.py — AI-Assisted Storyboard & 3D Animatic Assembler AnD os v1.2.0 — Studio Production & Narrative Layer (Island 4 & |
| `hybrid_comfyui_render.py` | hybrid_comfyui_render.py — Multi-Pass 3D-to-AI Styler and ComfyUI Dispatcher AnD os v1.2.0 — Hybrid Production Layer (Island 7 & 3D Pipeline |
| `image_ocr.py` | image_ocr.py - Thin facade delegating to the canonical hub module. Audit R4, P3 (R4-DUP-1): the ftrack/mattermost/OCR stack lived in two liv |
| `link_graph_orphans.py` | link_graph_orphans.py — Idempotent attachment of isolated notes to the root and category hubs of Obsidian. Goal: 1. For each isolated note ( |
| `link_guard.py` | link_guard.py — Vault-wide wikilink integrity gate (CLI). AnD os v1.2.0 (R-2, 20.11). Named per the AGENTS.md Fast-Track contract ("sys_cli  |
| `manifest_projector.py` | manifest_projector.py — Root Manifest Projector (Single Source of Truth Guard). The canonical system manifest lives at and_os/etc/system.jso |
| `mattermost_inspector.py` | mattermost_inspector.py - Thin facade delegating to the canonical hub module. Audit R4, P3 (R4-DUP-1): the ftrack/mattermost/OCR stack lived |
| `mattermost_sync.py` | mattermost_sync.py - Thin facade delegating to the canonical hub module. Audit R4, P3 (R4-DUP-1): the ftrack/mattermost/OCR stack lived in t |
| `mirror_collector.py` | mirror_collector.py — Deterministic Monthly Telemetry Aggregator for AnD os (Island 6). Aggregates factual metrics across: 1. Studio Product |
| `notify_macos.py` | notify_macos.py — Нативный мост уведомлений macOS Notification Center (без звука). Принципы: Think in Code (Правило №16), Silent Native Aler |
| `obsidian_blueprint_generator.py` | obsidian_blueprint_generator.py — Generator of the reference architecture and plugins passport of Obsidian. AnD os v1.2.0 — Production Envir |
| `passport_sync_runner.py` | passport_sync_runner.py — Daily cron wrapper for the Island 7 passport sync. Runs the library-level PulsarPassportSync (and_os/lib/pulsar/pa |
| `pdf_twin_converter.py` | pdf_twin_converter.py — Automatic creation of informational Markdown twins for PDFs. Principle: Think in Code (Rule #16), Data Safety (Rule  |
| `post_prompt_planner.py` | post_prompt_planner.py — Automatic generator of process maps (Post-Prompt Execution Map / DAG Planner). Principle: Think in Code (Rule #16), |
| `postmortem_analyzer.py` | postmortem_analyzer.py — Production Bottleneck & Sprint Postmortem Analyzer AnD os v1.2.0 — Studio Production Layer (Island 5: Studio & Theor |
| `proc_mesh.py` | proc_mesh.py — Generation and reading of the virtual state space (/proc mesh). Principle: Think in Code (Rule #16), 0-Token State Reading, L |
| `project_manager.py` | project_manager.py — Universal Project & App Onboarding Dispatcher for AnD os v1.2.0. Automatically registers new projects in Nero/pulsar (I |
| `project_registry.py` | project_registry.py — Unified Registry of External Software Systems and Web Services, ANDREY OS (v1.1.0). Catalogs all autonomous external s |
| `project_skeleton.py` | project_skeleton.py — Reference project skeleton generator (Skeleton Engine). AnD os v1.2.0 — Island 9 (Xcode / iOS Game Engineering) & Isla |
| `projects_registry_sync.py` | projects_registry_sync.py — External Project Registry Regenerator (SSoT sync). Regenerates and_os/srv/projects_registry.json from live sourc |
| `publish_doc.py` | publish_doc.py — Publication-grade Markdown to HTML/PDF publisher. Part of the document-hub skill (Contour: Publication, v1.1). Reverses the |
| `quick_find.py` | quick_find.py — Fast Knowledge Retrieval Tool with Okapi BM25 & Bilingual Expansion AnD os v1.2.0 — Think in Code Knowledge Retrieval Engine |
| `quick_verify.py` | quick_verify.py - Fast Pre-Flight Verification Loop for AnD os. Inspired by Everything-Claude-Code verification principles and adapted for m |
| `refactor_cleaner.py` | refactor_cleaner.py - Safe Refactoring and Dead Code Cleaner for AnD os v1.2.0. Analyzes Python & Swift ASTs for unused functions, dead code |
| `register_component.py` | Component Lifecycle & Registration Engine (register_component.py) AnD os v1.2.0 - Modular Architecture Infrastructure The automated tool for |
| `rules_compiler.py` | rules_compiler.py — Fast Rules Index Compiler for AnD os (v2, audit R2 P3). Compiles the canonical manifest (and_os/etc/system.json — SSoT)  |
| `rules_fulltext_expander.py` | rules_fulltext_expander.py — Canonical Rule Section Restorer & Consistency Guard. Restores missing "### Правило N:" sections in .opencode/ru |
| `run_tests.py` | run_tests.py — Canonical AnD os test-suite runner. Single entrypoint for the full canonical suite (audit R4 P1; evolved in P11; consolidated |
| `safe_snapshot.py` | safe_snapshot.py — Management of system state snapshots (APFS Local Snapshot & State Snapshots). Principles: APFS Native CoW (Rule #42, #43) |
| `schema_validator.py` | schema_validator.py — IPC response schema validation engine for system modules (Pydantic / Schema Engine). Principle: Data Contract Validati |
| `script_bible_extractor.py` | script_bible_extractor.py — Narrative IP & Script Bible Entity Extractor AnD os v1.2.0 — Narrative & Creative Layer (Island 4: Story & Books |
| `script_chunker.py` | script_chunker.py — the tool of the smart extraction of the fragments from the large texts/scripts/books. The principle: Think in Code (Rule |
| `sec_audit.py` | sec_audit.py - Security Audit & OWASP Top-10 / Injection Scanner for AnD os. Performs AST and heuristic analysis on Python, Swift, Shell, an |
| `session_gate.py` | session_gate.py — Universal Session Gate & Domain Anchor Beacon. Acts as a SessionStart lifecycle hook for Antigravity & LLM agents. Injects |
| `skill_bus.py` | skill_bus.py — Microkernel Skill Bus & Interop Engine (AnD os v1.2.0) Universal gateway for all 50 system skills: - inspect: zero-token arch |
| `skill_count_projector.py` | skill_count_projector.py — Single-source-of-truth projector for the active-skills count (R-4, 20.11: closes the "skill-count drift" class —  |
| `skill_dormancy_checker.py` | Skill Usage & Dormancy Analyzer AnD os v1.2.0 - Skill Governance (Rule №18) Parses and_os/lib/skills/telemetry.md, matches against all regis |
| `sos_auditor.py` | sos_auditor.py — Skill Operating Stack (SOS) Parallel Multi-Core Auditor. High-speed parallel diagnostic engine for AnD os skills. Verifies  |
| `state_manager.py` | state_manager.py (v1.2.0) — Unified Domain State Manager (IPC Bus). Manages, persists, and reconciles lean JSON states across core domains:  |
| `statusline.py` | statusline.py — Dynamic kernel statusline (Runtime Statusline Beacon). AnD os v1.2.0 — Island 8 (Kernel & AND_Terminal :8099). Prints a comp |
| `sync_context.py` | sync_context.py — the automation of the synchronization of the CONTEXT.md in the Obsidian Vault. The principle: Think in Code (Rule #16). Us |
| `sync_preflight.py` | sync_preflight.py — Pre-flight scanner of changes and structure synchronizer of AnD os. Rule #47: Pre-Flight Context & Cross-Chat Delta Sync |
| `sync_service.py` | sync_service.py — High-speed session initialization service (Fast Session Init Service v2.0). Runs direct module imports in a single Python  |
| `sys_bus.py` | sys_bus.py — CLI Adapter for AnD os Canonical Event Journal. Part of AnD os System Binaries (and_os/bin/). Delegates 100% of journal writes  |
| `sys_cli.py` | sys_cli.py — Unified Modular Dispatcher of AnD os (Modular Core CLI). Consolidates all system scripts and core modules into a single CLI wit |
| `system_dashboard.py` | system_dashboard.py — The Autonomous Interactive TUI Dashboard (AnD os v1.2.0 Live Top). Principles: Think in Code (Rule #16), the Rich TUI  |
| `system_tools_map.py` | system_tools_map.py — The Automatic Generator of the Unified System Passport of the Toolkit and the Runtimes (Toolchain & Runtime Engine). T |
| `task_db_engine.py` | task_db_engine.py — Local Task Database and Vault Indexing Engine (SQLite Engine). Principle: Think in Code (Rule #16), Zero-Token Querying. |
| `tasks_bridge.py` | tasks_bridge.py — Analytical and Synchronization Gateway of the Production Pulse (Tasks & Production Pulse). Provides token-efficient (<50 t |
| `tdd_scaffold.py` | tdd_scaffold.py - TDD Test Scaffold Generator for AnD os (Python & Swift). Extracts classes, functions, and methods from source files and ge |
| `telemetry_compact.py` | telemetry_compact.py - Monthly compaction of the telemetry journal (audit R4, P10, R4-TEL-2). The live journal and_os/lib/skills/telemetry.m |
| `telemetry_logger.py` | telemetry_logger.py — telemetry journal writer (Rule #11, IPC Bus). Appends validated records to and_os/lib/skills/telemetry.md without load |
| `temporal_consistency_guard.py` | temporal_consistency_guard.py — Frame Deflicker & Temporal Consistency Checker AnD os v1.2.0 — Quality & Animation Gate (Island 7 & Producti |
| `tg_career_fetcher.py` | tg_career_fetcher.py — Hybrid Telegram Career Ingestion Engine. Part of career-radar ecosystem | Rule #56 (No Hallucinations) & Rule #16 (To |
| `trim_output.py` | trim_output.py — Sandbox CLI execution wrapper with automatic log truncation (Rule #24). Keeps Head (first N lines) + Tail (last M lines), f |
| `ui_inspector.py` | ui_inspector.py — High-efficiency inspector of GUI/Dash/HTML components (ANDREY OS). Allows, without loading hundreds of code lines into the |
| `vacuum_cleaner.py` | vacuum_cleaner.py — AnD os System Sanitizer & Junk Collector (v1.1.0). Cleans the Obsidian Vault and the Pulsar ecosystem from junk artifact |
| `validate_system.py` | validate_system.py — Modular master dispatcher of the self-diagnostics and audit of AnD os. Health Grid architecture (Ring 0 - Ring 4): - Ri |
| `vault_guard_hook.py` | vault_guard_hook.py — Hardware-Level PreToolUse Governance Hook. Implements Dual-Speed Governance (Rule #19 Invariant): - Fast-Track (Core,  |
| `vfs_bridge.py` | vfs_bridge.py — CLI Router and Bridge for VFS Subsystem in AnD os v1.2.0. Part of AnD os Binary Bridges (and_os/bin/). Commands: sys_cli.py  |
| `video_harness.py` | video_harness.py — Autonomous technical QC validator for video and passes (Video E2E Harness). AnD os v1.2.0 — Island 7 & 5 (Pulsar & CG Pro |
| `video_scenes.py` | video_scenes.py — The selective media analysis of the video via the FFmpeg (Scene Detection). A part of the standard Think in Code (Rule #16 |
| `web_perf_baseline.py` | web_perf_baseline.py — Deterministic HTTP performance baseline & regression. Part of the ui-inspector skill (Contour B: Evidence-Based QA, v |
| `weeek_sync.py` | Weeek Sync — extraction and analytics of the tasks from Weeek (Studio). Works without an API key via direct reading of the open Safari tabs ( |
| `xl_analyze.py` | Excel/Google Sheets analyzer: reading formulas, links, structure. Run: python3 xl_analyze.py <path to file> [--sheet name] [--formulas] [--s |
| `yt_analyze.py` | YouTube video data extraction. python3 yt_analyze.py <url> --transcript  — transcript python3 yt_analyze.py <url> --info        — metadata p |

---

## 🧠 5. Declarative Skills (and_os/lib/skills/ — 51 skills)

| Skill | Purpose & Routing |
| :--- | :--- |
| `[[and_os/lib/skills/ai-rule/SKILL|ai-rule]]` | Use when creating, testing, or updating canonical 5-part system rules in .opencode/rules.md per the Rule #41 Governance Gate. |
| `[[and_os/lib/skills/api-contract-generator/SKILL|api-contract-generator]]` | Use when generating strict JSON schema contracts, TypeScript interfaces, and inter-process communication specs between services. |
| `[[and_os/lib/skills/board-analyzer/SKILL|board-analyzer]]` | Use when parsing and analyzing visual boards (Canvas, Miro, FigJam) to extract cards, connections, and structured task graphs. |
| `[[and_os/lib/skills/book-pipeline/SKILL|book-pipeline]]` | Use when ingesting book notes into actionable 8-block summaries, transforming business/management books into execution toolkits (Monday-morning decisi |
| `[[and_os/lib/skills/career-radar/SKILL|career-radar]]` | Use when executing weekly executive market intelligence scans, vacancy scoring, and career opportunity radar for System Architect across CG animation,  |
| `[[and_os/lib/skills/cg-content/SKILL|cg-content]]` | Use when drafting thought-leadership articles, case studies, analytical breakdowns, batch CG marketing assets, shot breakdowns, and multi-platform pro |
| `[[and_os/lib/skills/cg-core-consulting/SKILL|cg-core-consulting]]` | Use when auditing animation studio pipelines, diagnosing production bottlenecks, or formulating B2B CG advisory curricula. |
| `[[and_os/lib/skills/cg-pipeline/SKILL|cg-pipeline]]` | Use when executing multi-DCC production pipeline steps: procedural modeling, scene assembly, USD overrides, and master cutting. |
| `[[and_os/lib/skills/clipping-finder/SKILL|clipping-finder]]` | Use when searching across raw clippings, web extracts, and unstructured articles in Clippings/ to extract core insights for active tasks. |
| `[[and_os/lib/skills/comfy-studio/SKILL|comfy-studio]]` | Use when designing, compiling, or refactoring JSON node graphs for ComfyUI, or batch executing 3D neural passes, depth maps, and latent upscaling via  |
| `[[and_os/lib/skills/context-compressor/SKILL|context-compressor]]` | Use when compressing large multi-file directories and codebase contexts into minimal-token Markdown bundles per Rule #44. |
| `[[and_os/lib/skills/cut-suite/SKILL|cut-suite]]` | Use when directing hybrid 2D/3D/AI animatics, planning camera keyframe layouts, cutting shot timelines, calculating frame handles, or interchanging ED |
| `[[and_os/lib/skills/deep-research/SKILL|deep-research]]` | Use when conducting multi-source deep research on a technical or industry topic: outline with per-item fields, parallel subagent retrieval with resume |
| `[[and_os/lib/skills/dev-flow/SKILL|dev-flow]]` | Use when planning multi-step software engineering cycles, designing test coverage matrices, managing git branches, or authoring, reviewing, and refact |
| `[[and_os/lib/skills/document-hub/SKILL|document-hub]]` | Use when converting, extracting text, OCR parsing, or restructuring PDFs, DOCX, and spreadsheet documents, or producing publication-ready HTML/PDF fro |
| `[[and_os/lib/skills/employee-hub/SKILL|employee-hub]]` | Use when evaluating artist competency scorecards, aggregating crew feedback, and auditing workload across studio departments. |
| `[[and_os/lib/skills/external-skills-gateway/SKILL|external-skills-gateway]]` | Use when searching, inspecting, filtering, or integrating open-source agent skills from skills.sh, Vercel Labs, and GitHub into AnD os. |
| `[[and_os/lib/skills/file-lifecycle/SKILL|file-lifecycle]]` | Use when classifying and routing newly drafted notes, reports, and knowledge assets to their canonical Obsidian Vault folders, or updating CONTEXT.md  |
| `[[and_os/lib/skills/ftrack-sync/SKILL|ftrack-sync]]` | Use when synchronizing project milestones, shot progress, asset statuses, and task assignments from Ftrack API for Mars and Kot productions. |
| `[[and_os/lib/skills/github-ops/SKILL|github-ops]]` | Use when searching GitHub repositories, inspecting issues, analyzing pull requests (including modernizing stale PRs), checking CI/CD workflow runs, re |
| `[[and_os/lib/skills/goal-system/SKILL|goal-system]]` | Use when setting SMART annual, quarterly, or life milestone goals across career, health, creative, family, and wealth domains; auditing goal achieveme |
| `[[and_os/lib/skills/health-hub/SKILL|health-hub]]` | Use when analyzing laboratory blood biomarkers, ultrasound findings, clinical consultation notes, and preventive health panels, or computing cross-dom |
| `[[and_os/lib/skills/higgsfield-seedance-prompt/SKILL|higgsfield-seedance-prompt]]` | Use when engineering cinematic camera movement, lighting, and temporal coherence prompts for Higgsfield and Seedance video models. |
| `[[and_os/lib/skills/houdini-bridge/SKILL|houdini-bridge]]` | Use when controlling a running Houdini 22.x instance through the fxhoudinimcp MCP bridge on loopback: scene builds, node and parameter edits, frame co |
| `[[and_os/lib/skills/investor-outreach/SKILL|investor-outreach]]` | Use when composing personalized investor pitches, grant applications (IRI, ON Media), and follow-up investment communications. |
| `[[and_os/lib/skills/ios-game-builder/SKILL|ios-game-builder]]` | Use when prototyping, engineering, compiling, and debugging native iOS/macOS games and apps in Swift, SwiftUI, and SpriteKit without user programming. |
| `[[and_os/lib/skills/llm-council/SKILL|llm-council]]` | Use when orchestrating multi-agent consensus debates, adversarial evaluations, multi-model synthesis on critical decisions, obtaining an independent c |
| `[[and_os/lib/skills/mattermost-sync/SKILL|mattermost-sync]]` | Use when synchronizing studio chat channels, compiling daily communication digests, and isolating cross-departmental blockers. |
| `[[and_os/lib/skills/meetings-hub/SKILL|meetings-hub]]` | Use when decomposing production meeting transcripts into prioritized action points with assignees and deadline milestones. |
| `[[and_os/lib/skills/memory/SKILL|memory]]` | Use when orchestrating closed-loop memory in AnD os: running Pre-flight Recall to retrieve negative constraints, Post-flight Learning to crystallize s |
| `[[and_os/lib/skills/negotiation/SKILL|negotiation]]` | Use when preparing for any high-stakes dialogue: commercial negotiations, salary and offer talks, job interviews (candidate or interviewer side), lett |
| `[[and_os/lib/skills/obsidian-bases/SKILL|obsidian-bases]]` | Use when creating, validating, and maintaining Obsidian Bases (.base files) with views, reactive filters, formulas, and summaries for database-like ta |
| `[[and_os/lib/skills/openmontage-builder/SKILL|openmontage-builder]]` | Use when performing generative video assembly, timeline orchestration, reference-guided pacing cuts, and automated hardware-accelerated FFmpeg editing |
| `[[and_os/lib/skills/portfolio-summary/SKILL|portfolio-summary]]` | Use when analyzing personal multi-currency financial balances, investment brokerage assets, and monthly cashflow dynamics. |
| `[[and_os/lib/skills/prompt-improver/SKILL|prompt-improver]]` | Use when adapting Andrey's raw, handwritten, or voice-dictated prompts into precise structured agent tasks (5-block spec), or clarifying underspecifie |
| `[[and_os/lib/skills/reverse-engineer-anything/SKILL|reverse-engineer-anything]]` | Use when reverse-engineering native, managed, Electron/JavaScript, packaged, firmware, SQLite, or browser targets, or deconstructing foreign codebases |
| `[[and_os/lib/skills/skill-creator/SKILL|skill-creator]]` | Use when creating, validating, linting, updating, dieting, or routing-evaluating skills in AnD os. Enforces SKILL_MODULE_ABI v2.1, 8-Island architectu |
| `[[and_os/lib/skills/skill-router/SKILL|skill-router]]` | Use when arbitrating between competing domain skills and routing complex multi-step user prompts to the single primary skill. |
| `[[and_os/lib/skills/status-report/SKILL|status-report]]` | Use when compiling executive producer status reports for Mars and Kot animation features with department velocity and dependencies, capturing operatio |
| `[[and_os/lib/skills/story-dev/SKILL|story-dev]]` | Use when developing dramaturgical animation narratives, character arcs, loglines, synopses, worldbuilding rules, step outlines, or distilling narrativ |
| `[[and_os/lib/skills/system-architect/SKILL|system-architect]]` | Use when bootstrapping new software projects, web services, games, 3D pipelines, or core modules. Enforces Spec-Before-Code, C4/ADR design docs, and r |
| `[[and_os/lib/skills/system-audit/SKILL|system-audit]]` | Use when running full 5-ring Health Grid integrity validations across filesystem syntax, knowledge graph, AST, and background daemons, auditing the in |
| `[[and_os/lib/skills/ta-bu-plan/SKILL|ta-bu-plan]]` | Use when reviewing or expanding Ta-Bu animation startup strategy, challenging a proposed strategic direction (forcing questions), unit economics, corp |
| `[[and_os/lib/skills/task-graph/SKILL|task-graph]]` | Use when querying the SQLite task index, managing priority blockers, computing dependency DAGs across all vault markdown TODOs, or publishing compiled |
| `[[and_os/lib/skills/tax-compliance/SKILL|tax-compliance]]` | Use when calculating individual entrepreneur (IP) taxes, self-employed declarations, social fund payments, and accounting records. |
| `[[and_os/lib/skills/teach-hub/SKILL|teach-hub]]` | Use when constructing interactive training paths for studio staff, mentoring trajectories, mission-based curricula, or B2B educational consulting cont |
| `[[and_os/lib/skills/temporal-consistency-guard/SKILL|temporal-consistency-guard]]` | Use when verifying visual and narrative continuity, character wardrobe constancy, and lighting consistency across AI video shots. |
| `[[and_os/lib/skills/training-hub/SKILL|training-hub]]` | Use when retrieving nocturnal HRV, sleep architecture, resting HR, and ACWR training load indices from telemetry_sync Connect, or designing structured maratho |
| `[[and_os/lib/skills/uc-diet-planning/SKILL|uc-diet-planning]]` | Use when structuring medical nutrition protocols, gut-soothing weekly menus, and anti-inflammatory diets for chronic_condition (UC). |
| `[[and_os/lib/skills/ui-inspector/SKILL|ui-inspector]]` | Use when inspecting frontend web UI applications, probing HTTP ports for 200 OK liveness, verifying stylesheet assets, or running evidence-based QA on |
| `[[and_os/lib/skills/weeek-hub/SKILL|weeek-hub]]` | Use when synchronizing Weeek project workspaces, identifying overdue task blockers, or balancing sprint kanban boards. |

---
[[SYSTEM_MAP|← Master Atlas SYSTEM_MAP.md]] | [[SYSTEM|← Master Manifest SYSTEM.md]]
