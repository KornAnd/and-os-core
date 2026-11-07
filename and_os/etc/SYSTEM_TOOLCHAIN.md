---
tags:
  - system
  - toolchain
  - context
  - runtime
created: 2026-11-06 11:03:14
---

# 🛠️ SYSTEM TOOLCHAIN — Runtime Standard & Toolchain Specification AnD os v8.1

> **Specification for AI Agents and Developers:** Canonical specification of programming language versions, installed libraries, 105 core scripts, and 65 active skills.  
> **Automated Refresh:** `python3 and_os/bin/sys_cli.py env` or `python3 and_os/bin/system_tools_map.py --build`

---

## ⚙️ 0. Runtime Environment Standard

| Language / Runtime | Current Version | Target Standard | Executable Path | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Python** | `3.9.6` | `>=3.11 (Recommended 3.14.x)` | `/Library/Developer/CommandLineTools/usr/bin/python3` | 🟢 Active |
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
| **FFmpeg** | `ffmpeg version 9.0.2 Copyright (c) 2000-2026 the FFmpeg developers` | Декодирование, нарезка видео/аудио, конформ таймлайнов |
| **Tesseract OCR** | `tesseract 5.5.4` | Оптическое распознавание текста со сканов и скриншотов |
| **yt-dlp** | `2026.10.26` | Загрузка медиа и транскриптов YouTube (`yt_analyze.py`) |
| **uv** | `uv 0.13.6 (Homebrew 2026-10-26 aarch64-apple-darwin)` | Ультрабыстрый менеджер пакетов и виртуальных окружений Python |
| **GitHub CLI (gh)** | `gh version 2.103.3 (2026-10-26)` | Управление репозиториями, PR и релизами GitHub |
| **jq** | `jq-1.8.2` | Потоковая фильтрация и парсинг JSON в терминале |
| **SQLite3** | `3.54.0 2026-04-09 12:25:13 8fa8248e303219400c646a885e36dfc52eae33d83f4412e3f369b2be5373aapl (64-bit)` | Встроенное хранилище индексов и задач (`task_vault.db`) |
| **tmux** | `tmux 3.8` | Мультиплексор терминальных сессий |

---

## 🎨 2. DCC, 3D & Creative Suites (Muscle Realm)

| Software / Suite | Version / Status | Production Domain / Role |
| :--- | :--- | :--- |
| **Blender** | `Blender 5.1.1` | 3D-моделирование, процедурные ассеты, рендер (`cg_workspace`) |
| **Houdini** | `22.0.466` | Процедурный FX/динамика, Solaris, USD пайплайн |
| **DaVinci Resolve** | `21.1.1` | Цветокоррекция, финальный монтаж, конформ шотов (`openmontage-builder`) |
| **Xcode** | `27.2` | Нативная разработка iOS/macOS игр и приложений (Остров 9) |
| **Comfy Desktop** | `1.1.8` | Нейросетевая генерация и стилизация шотов (ComfyUI / ControlNet) |
| **Unity Hub** | `3.22.5` | Менеджер игровых движков Unity (Standby / Cross-platform) |

---

## 📱 3. Desktop Applications & System Bridges

| Application | Version / Status | System Interaction |
| :--- | :--- | :--- |
| **Obsidian** | `1.6.7` | Суверенное когнитивное пространство (Brain Realm) |
| **Mattermost** | `6.3.2` | Корпоративный мессенджер Production Studio (`mattermost_sync.py`) |
| **Telegram** | `13.1.0` | Каналы, боты и оперативная коммуникация (`tg_bot_app`) |
| **Docker** | `4.97.0` | Контейнеризация микросервисов и баз данных |

---

### 📦 Installed Python Packages & Modules (12 total)

#### 🔹 Security, Crypto & System

| Package / Module | Version | Architectural Role in AnD os |
| :--- | :--- | :--- |
| `platformdirs` | `4.4.0` | System utility |

#### 🔹 Build & Core Infrastructure

| Package / Module | Version | Architectural Role in AnD os |
| :--- | :--- | :--- |
| `pip` | `21.2.4` | System utility |
| `setuptools` | `58.0.4` | System utility |
| `virtualenv` | `20.35.4` | System utility |
| `wheel` | `0.37.0` | System utility |

#### 🔹 Other Utilities

| Package / Module | Version | Architectural Role in AnD os |
| :--- | :--- | :--- |
| `altgraph` | `0.17.2` | System utility |
| `distlib` | `0.4.0` | System utility |
| `filelock` | `3.19.1` | System utility |
| `future` | `0.18.2` | System utility |
| `macholib` | `1.15.2` | System utility |
| `six` | `1.15.0` | System utility |
| `typing_extensions` | `4.15.0` | System utility |

---

## ⚡ 4. Core Executable Scripts (and_os/bin/ & sbin/ — 105 scripts)

| Script | Purpose & Description |
| :--- | :--- |
| `agent_handoff.py` | agent_handoff.py - Validator and Generator for AnD os Subagent Handoff Protocol. Ensures zero-context loss during inter-agent transitions co |
| `api_contract_generator.py` | api_contract_generator.py — Typed API & Microkernel Contract Generator AnD os v8.1 — System Engineering Layer (Type-Safe Contracts & Schemas |
| `app_bridge.py` | app_bridge.py — Диспетчер бесшовного взаимодействия Obsidian и Внешних Проектов (v1.0.0). Управляет регистрацией проектов, валидацией их здо |
| `app_deconstructor.py` | app_deconstructor.py — Automated Application & Service Architecture Deconstructor AnD os v8.1 — System Engineering Layer (Clean Architecture |
| `app_quick_check.py` | Python CLI Automation Script |
| `architect_engine.py` | architect_engine.py — Sovereign System Architecture & Project Scaffolding Engine. AnD os v9.2 — Master Systems Architect Module (Island 8 /  |
| `artifact_capture.py` | artifact_capture.py - Visual Artifact & Diagnostic State Capture Engine on Failure. Captures: 1. macOS desktop/window screenshot via /usr/sb |
| `asset_indexer.py` | Asset Indexer for ANDREY OS (v1.0.0) Scans non-MD assets (images, archives, audio, binaries, code exports), maps them to parent context file |
| `audit_graph_orphans.py` | audit_graph_orphans.py — Точный сканер графовой связности Obsidian Vault. Находит файлы, которые в визуальном графе Obsidian отображаются си |
| `audit_tags_links.py` | audit_tags_links.py — проверка и доставка тегов каталога и навигационных ссылок CONTEXT. Принцип: Think in Code (Правило №16) и Правило №1 ( |
| `backup_engine.py` | backup_engine.py — Enterprise Backup Engine for AnD os v8.5. Features: - 100% Full Obsidian Vault backup (All knowledge domains, configs, co |
| `board_parser.py` | Board Parser & Visual Semantic Extractor (Miro, Holst, FigJam, Schemas) AnD os v8.1 - Think in Code Infrastructure Поддерживает: 1. Визуальн |
| `bootstrap_system.py` | bootstrap_system.py — Zero-Touch System Bootstrap & Platform Provisioning Engine. AnD os v8.1 (Rule №48: Zero-Cost Cross-Platform Unix Compa |
| `budget_calc.py` | budget_calc.py — Единый CLI-модуль расчёта бюджетов и смет (Think in Code / IPC Bus). Принцип: Zero-Token Computation. Расчёт ставок, смен и |
| `build_native.py` | build_native.py — Системный компилятор Python-проектов в нативные бинарники (Правило №32). Поддерживаемые компиляторы: - PyInstaller (основн |
| `build_resolver.py` | build_resolver.py — Автономный резолвер ошибок сборки с минимальными диффами (Minimal Diffs). AnD os v8.4 — Остров 8 (Kernel & Compiler) ⟷ О |
| `career_radar.py` | career_radar.py — Executive Market Radar & Opportunity Matcher Part of AnD os v9.2 | Rule #16 (Think-in-Code), Rule #54 (Zero-Orphans), Rule |
| `cg_bridge.py` | CG Pipeline Integration Bridge (cg_bridge.py) AnD os v8.1 - Think in Code Infrastructure Обеспечивает надежный, токеноэкономичный и воспроиз |
| `checkpoint_manager.py` | checkpoint_manager.py - High-Performance APFS CoW & Git State Checkpoint Engine for AnD os. Combines Apple File System instantaneous copy-on |
| `clean_links.py` | clean_links.py — безопасная нормализация ссылок на несуществующие картинки. Proxy-shim к монолитной библиотеке and_os.lib.vault. |
| `closed_loop.py` | closed_loop.py — Единый Мастер-Диспетчер Замкнутого Контура (Closed-Loop Sovereign OS Stack v1.0). Обеспечивает сквозную регистрацию артефак |
| `codemap_engine.py` | codemap_engine.py — Генератор сверхлегких архитектурных карт кода (Codemaps Engine). AnD os v8.4 — Остров 8 (Kernel & System Compiler). Обес |
| `comfy_graph.py` | comfy_graph.py — ComfyUI Graph Analysis, Validation, Visualization, and Sync Engine (Think in Code). Supported Formats: 1. Web UI Workflow J |
| `comfy_node_registry.py` | comfy_node_registry.py — Active ComfyUI Node Version Registry & Validator (Rule #45 & Update Guard). Principles: Think in Code (Rule #16), 1 |
| `context_budget_guard.py` | context_budget_guard.py — Страж бюджета контекста и фазовый компактор AnD os v8.4. Остров 8 (Kernel Core) ⟷ Инструментальный рантайм агента. |
| `context_bundler.py` | Task Context Bundler & Output Trimming Utility AnD os v8.1 - Think in Code Context Squeezer Collects minimum sufficient context for tasks (s |
| `context_mode_manager.py` | context_mode_manager.py - Context Mode Switcher for AnD os v8.5. Manages active behavioral presets (dev, research, review) for LLM agents. |
| `context_router.py` | context_router.py — Умная быстрая БД и маршрутизатор контекстных файлов ANDREY OS (v1.0.0). Индексирует все CONTEXT.md в Vault, ведет реестр |
| `continuous_learner.py` | continuous_learner.py — Интеллектуальный компилятор опыта сессий для AnD os v8.4. Остров 8 (Kernel & Compiler) ⟷ Остров 1 & 6 (Knowledge Rea |
| `convert_doc.py` | convert_doc.py — Универсальный конвертер документов в чистый Markdown для LLM на базе Microsoft MarkItDown с надежным fallback-контуром. Под |
| `dag_planner.py` | dag_planner.py - DAG Phase Planner & Acceptance Criteria Engine for AnD os. Enforces Rule #20 and Rule #36 (Atomic Phased Execution & DoD Ch |
| `dash_smoke_test.py` | dash_smoke_test.py — Headless Smoke-Tester для веб-приложений Dash / Plotly (Mars, Kot, Dino и др.). Проверяет: 1. Синтаксическую целостност |
| `dependency_engine.py` | dependency_engine.py — Unified System Dependency Analyzer & Cascade Synchronizer. AnD os v8.1 (Pillar II & VI: Full Information Dependency & |
| `dev_flow.py` | dev_flow.py — Модульный CLI-оркестратор строгой поэтапной разработки AnD os. Управляет сессией разработки через детерминированный FSM и врем |
| `doc_analyze.py` | doc_analyze.py — универсальный анализатор документов, таблиц, PDF и изображений. Реализует принцип Think in Code (Правило №16) и Context Bud |
| `docs_sync.py` | docs_sync.py - Automatic Runbook and Documentation Synchronizer for AnD os v8.5. Parses SSOT configurations (system.json, sys_cli.py, root_c |
| `editorial_otio_conform.py` | editorial_otio_conform.py — OpenTimelineIO Editorial Conform Engine (AnD os v8.1) Conforms editorial timelines, handles EDL/XML/OTIO interch |
| `eval_engine.py` | eval_engine.py - Eval-Driven Development (EDD) Framework for AnD os. Inspired by Everything-Claude-Code eval harness and adapted for determi |
| `finance_bridge.py` | finance_bridge.py — Аналитический и Синхронизационный Шлюз Финансового Капитала (AnD os v8.1). Обеспечивает 100% локальный, герметичный (Air |
| `fix_webdav_sync_issues.py` | fix_webdav_sync_issues.py — Комплексное исправление проблемных путей и файлов для стабильной синхронизации WebDAV: 1. Замена симлинков blend |
| `ftrack_cache.py` | Модуль кеширования выгрузок Ftrack API для снижения трат токенов и ускорения анализа. Функции: query_cached(session, query_str, cache_key, m |
| `ftrack_gantt_exporter.py` | ftrack_gantt_exporter.py — Модуль точечной выгрузки данных Ftrack для Диаграммы Ганта (v2.0.0). Поддерживает фильтрацию по проектам (--proje |
| `ftrack_inspector.py` | ftrack_inspector.py — Анализатор структуры и поэтапный бережный забор данных из Ftrack. Возможности: 1. inspect: глубокий аудит структуры пр |
| `ftrack_report.py` | Ftrack → таблицы → статус-отчёт (Кот / Марс). Режимы: python3 ftrack_report.py --project kot --export        # выгрузить сырые данные в CSV  |
| `ftrack_sync.py` | Синхронизация Ftrack → Obsidian для проектов Кот учёный и Мотомарс ПМ. Использует единый оптимизированный аналитический движок ftrack_report |
| `telemetry_sync_sync.py` | Расширенная синхронизация telemetry_sync Connect → Obsidian (health.md, telemetry_sync.md, sport.md). Извлекает исчерпывающий пласт биометрии и аналитики: - |
| `gen_context.py` | Генератор контекста для внешних LLM (ChatGPT, Claude, Gemini). Собирает все CONTEXT.md из хранилища Obsidian в единый файл, оптимизированный |
| `graph_builder.py` | graph_builder.py — Движок генерации и оркестрации графов задач (Execution DAG). Часть стандарта Task Execution Graph (Правило №20). Генериру |
| `health_bridge.py` | health_bridge.py — Единый аналитический и синхронизационный шлюз здоровья семьи ANDREY OS (AnD os v8.1). Стандарты: - Правило №7: Двухконтур |
| `hybrid_animatic_director.py` | hybrid_animatic_director.py — AI-Assisted Storyboard & 3D Animatic Assembler AnD os v8.1 — Studio Production & Narrative Layer (Island 4 & I |
| `hybrid_comfyui_render.py` | hybrid_comfyui_render.py — Multi-Pass 3D-to-AI Styler and ComfyUI Dispatcher AnD os v8.1 — Hybrid Production Layer (Island 7 & 3D Pipeline)  |
| `image_ocr.py` | OCR-анализатор изображений через tesseract. Использует tesseract OCR с языковыми пакетами rus+eng. Установка: brew install tesseract tessera |
| `link_graph_orphans.py` | link_graph_orphans.py — Идемпотентная привязка изолированных заметок к корневым и категориальным хабам Obsidian. Цель: 1. Для каждой изолиро |
| `mattermost_inspector.py` | mattermost_inspector.py — Анализатор структуры, аудитор и staged-экстрактор срезов Mattermost. Архитектурный стандарт: AnD os v8.1 (Правило  |
| `mattermost_sync.py` | Mattermost API → дайджест сообщений и фоллоу-апы (Studio). Режимы: python3 mattermost_sync.py --teams                                   # спис |
| `mirror_collector.py` | mirror_collector.py — Deterministic Monthly Telemetry Aggregator for AnD os (Island 6). Aggregates factual metrics across: 1. Studio Product |
| `notify_macos.py` | notify_macos.py — Нативный мост уведомлений macOS Notification Center (без звука). Принципы: Think in Code (Правило №16), Silent Native Aler |
| `obsidian_blueprint_generator.py` | obsidian_blueprint_generator.py — Генератор эталонного паспорта архитектуры и плагинов Obsidian. AnD os v8.1 — Production Environment Bluepr |
| `pdf_twin_converter.py` | pdf_twin_converter.py — Автоматическое создание информационных Markdown-двойников для PDF. Принцип: Think in Code (Правило №16), Безопасност |
| `post_prompt_planner.py` | post_prompt_planner.py — Автоматический генератор карт процессов (Post-Prompt Execution Map / DAG Planner). Принцип: Think in Code (Правило  |
| `postmortem_analyzer.py` | postmortem_analyzer.py — Production Bottleneck & Sprint Postmortem Analyzer AnD os v8.1 — Studio Production Layer (Island 5: Studio & Theory  |
| `proc_mesh.py` | proc_mesh.py — Генерация и чтение виртуального пространства состояния (/proc mesh). Принцип: Think in Code (Правило №16), 0-Token State Read |
| `project_manager.py` | project_manager.py — Universal Project & App Onboarding Dispatcher for AnD os v8.5. Automatically registers new projects in Nero/pulsar (Isl |
| `project_registry.py` | project_registry.py — Единый Реестр Внешних Программных Систем и Веб-Сервисов ANDREY OS (v1.0.0). Каталогизирует все автономные внешние серв |
| `project_skeleton.py` | project_skeleton.py — Генератор эталонных каркасов проектов (Skeleton Engine). AnD os v8.4 — Остров 9 (Xcode / iOS Game Engineering) & Остро |
| `quick_find.py` | quick_find.py — Fast Knowledge Retrieval Tool with Okapi BM25 & Bilingual Expansion AnD os v8.1 — Think in Code Knowledge Retrieval Engine ( |
| `quick_verify.py` | quick_verify.py - Fast 6-Phase Pre-Flight Verification Loop for AnD os. Inspired by Everything-Claude-Code verification principles and adapt |
| `refactor_cleaner.py` | refactor_cleaner.py - Safe Refactoring and Dead Code Cleaner for AnD os v8.5. Analyzes Python & Swift ASTs for unused functions, dead code b |
| `register_component.py` | Component Lifecycle & Registration Engine (register_component.py) AnD os v8.1 - Modular Architecture Infrastructure Автоматизированный инстр |
| `rules_compiler.py` | rules_compiler.py — Fast Rules Index Compiler for AnD os v8.5. Compiles SYSTEM.md and .opencode/rules.md into a high-density, token-efficien |
| `safe_snapshot.py` | safe_snapshot.py — Управление снимками состояния системы (APFS Local Snapshot & State Snapshots). Принципы: APFS Native CoW (Правило №42, №4 |
| `schema_validator.py` | schema_validator.py — Движок валидации IPC-схем ответов системных модулей (Pydantic / Schema Engine). Принцип: Data Contract Validation. Про |
| `script_bible_extractor.py` | script_bible_extractor.py — Narrative IP & Script Bible Entity Extractor AnD os v8.1 — Narrative & Creative Layer (Island 4: Story & Books)  |
| `script_chunker.py` | script_chunker.py — инструмент умного извлечения фрагментов из крупных текстов/сценариев/книг. Принцип: Think in Code (Правило №16) & Contex |
| `sec_audit.py` | sec_audit.py - Security Audit & OWASP Top-10 / Injection Scanner for AnD os. Performs AST and heuristic analysis on Python, Swift, Shell, an |
| `session_gate.py` | session_gate.py — Universal Session Gate & Domain Anchor Beacon (AnD os v9.0). Acts as a SessionStart lifecycle hook for Antigravity & LLM a |
| `skill_bus.py` | skill_bus.py — Microkernel Skill Bus & Interop Engine (AnD os v8.1) Universal gateway for all 58 system skills: - inspect: zero-token archit |
| `skill_dormancy_checker.py` | Skill Usage & Dormancy Analyzer AnD os v8.1 - Skill Governance (Rule №18) Parses and_os/lib/skills/telemetry.md, matches against all registe |
| `sos_auditor.py` | sos_auditor.py — Skill Operating Stack (SOS) Parallel Multi-Core Auditor. High-speed parallel diagnostic engine for AnD os skills. Verifies  |
| `state_manager.py` | state_manager.py (v1.2.0) — Unified Domain State Manager (IPC Bus). Manages, persists, and reconciles lean JSON states across core domains:  |
| `statusline.py` | statusline.py — Динамическая статус-строка ядра (Runtime Statusline Beacon). AnD os v8.4 — Остров 8 (Kernel & AND_Terminal :8099). Выводит к |
| `sync_context.py` | sync_context.py — автоматизация синхронизации CONTEXT.md в Obsidian Vault. Принцип: Think in Code (Правило №16). Использование: python3 sync |
| `sync_preflight.py` | sync_preflight.py — Пре-полетный сканер изменений и синхронизатор структуры AnD os. Правило №47: Pre-Flight Context & Cross-Chat Delta Synch |
| `sync_service.py` | sync_service.py — Высокоскоростной сервис инициализации сессии (Fast Session Init Service v2.0). Выполняет прямые импорты модулей в едином P |
| `sys_bus.py` | sys_bus.py — CLI Adapter for AnD os Canonical Event Journal. Part of AnD os System Binaries (and_os/bin/). Delegates 100% of journal writes  |
| `sys_cli.py` | sys_cli.py — Unified Modular Dispatcher of AnD os (Modular Core CLI). Consolidates all system scripts and core modules into a single CLI wit |
| `system_dashboard.py` | system_dashboard.py — Автономный Интерактивный TUI-Дашборд (AnD os v8.1 Live Top). Принципы: Think in Code (Правило №16), Rich TUI (Автономн |
| `system_tools_map.py` | system_tools_map.py — Автоматический Генератор Единого Системного Паспорта Инструментария и Рантаймов (Toolchain & Runtime Engine). Принцип: |
| `task_db_engine.py` | task_db_engine.py — Локальный Движок БД Задач и Индексации Vault (SQLite Engine). Принцип: Think in Code (Правило №16), Zero-Token Querying. |
| `tasks_bridge.py` | tasks_bridge.py — Аналитический и Синхронизационный Шлюз Производственного Пульса (Tasks & Production Pulse). Обеспечивает токеноэффективное |
| `tdd_scaffold.py` | tdd_scaffold.py - TDD Test Scaffold Generator for AnD os (Python & Swift). Extracts classes, functions, and methods from source files and ge |
| `telemetry_logger.py` | telemetry_logger.py — Модуль быстрых логов телеметрии (IPC Bus). Модульная программа для добавления валидированных записей в and_os/lib/skil |
| `temporal_consistency_guard.py` | temporal_consistency_guard.py — Frame Deflicker & Temporal Consistency Checker AnD os v8.1 — Quality & Animation Gate (Island 7 & Production |
| `tg_career_fetcher.py` | tg_career_fetcher.py — Automated Telegram Channels Ingestion Engine (AnD os v9.1). Part of career-radar ecosystem | Rule #59 (Official Proto |
| `trim_output.py` | trim_output.py — Обертка для песочного выполнения CLI-команд с авто-усечением логов (Правило №24). Сохраняет Head (первые N строк) + Tail (п |
| `ui_inspector.py` | ui_inspector.py — Высокоэффективный инспектор GUI/Dash/HTML компонентов (ANDREY OS). Позволяет без загрузки сотен строк кода в контекст моде |
| `vacuum_cleaner.py` | vacuum_cleaner.py — Системный Санитар и Сборщик Мусора AnD os (v1.0.0). Очищает хранилище Obsidian Vault и экосистему Pulsar от мусорных арт |
| `validate_system.py` | validate_system.py — Модульный мастер-диспетчер самодиагностики и аудита AnD os. Архитектура Health Grid (Ring 0 - Ring 4): - Ring 0: FSSynt |
| `vault_guard_hook.py` | vault_guard_hook.py — Hardware-Level PreToolUse Governance Hook (AnD os v9.0). Implements Dual-Speed Governance (Rule #19 Invariant): - Fast |
| `vfs_bridge.py` | vfs_bridge.py — CLI Router and Bridge for VFS Subsystem in AnD os v8.1. Part of AnD os Binary Bridges (and_os/bin/). Commands: sys_cli.py vf |
| `video_harness.py` | video_harness.py — Автономный валидатор технического ОТК видео и пассов (Video E2E Harness). AnD os v8.4 — Остров 7 & 5 (Pulsar & CG Product |
| `video_scenes.py` | video_scenes.py — Селективный медиа-анализ видео через FFmpeg (Scene Detection). Часть стандарта Think in Code (Правило №16). Фильтр FFmpeg  |
| `weeek_sync.py` | Weeek Sync — извлечение и аналитика задач из Weeek (Studio). Работает без API-ключа через прямое чтение открытых вкладок Safari (AppleScript L |
| `xl_analyze.py` | Анализатор Excel/Google Sheets: чтение формул, связей, структуры. Запуск: python3 xl_analyze.py <путь к файлу> [--sheet имя] [--formulas] [- |
| `yt_analyze.py` | Извлечение данных из YouTube видео. python3 yt_analyze.py <url> --transcript  — транскрипт python3 yt_analyze.py <url> --info        — метад |

---

## 🧠 5. Declarative Skills (and_os/lib/skills/ — 65 skills)

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
| `[[and_os/lib/skills/career-radar/SKILL|career-radar]]` | Weekly executive market radar and vacancy scoring engine for System Architect across CG animation, gamedev cinematics, streaming originals, and brand v |
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
| `[[and_os/lib/skills/goal-writer/SKILL|goal-writer]]` | Use when formulating SMART annual, quarterly, and life milestone goals across career, health, creative, and family domains. |
| `[[and_os/lib/skills/health-diagnostics-hub/SKILL|health-diagnostics-hub]]` | Use when analyzing laboratory blood biomarkers, ultrasound findings, clinical consultation notes, and preventive health panels. |
| `[[and_os/lib/skills/health-orchestrator/SKILL|health-orchestrator]]` | Use when computing cross-domain clinical health synthesis, orthopedics vs running cadence, and athletic recovery clearances. |
| `[[and_os/lib/skills/higgsfield-seedance-prompt/SKILL|higgsfield-seedance-prompt]]` | Use when engineering cinematic camera movement, lighting, and temporal coherence prompts for Higgsfield and Seedance video models. |
| `[[and_os/lib/skills/hybrid-animatic-director/SKILL|hybrid-animatic-director]]` | Use when directing hybrid 2D/3D/AI animatics, synthesizing shot transitions, and planning camera keyframe layouts. |
| `[[and_os/lib/skills/hybrid-comfyui-render/SKILL|hybrid-comfyui-render]]` | Use when batch executing 3D neural passes, depth maps, and latent upscaling via local ComfyUI workers. |
| `[[and_os/lib/skills/investor-outreach/SKILL|investor-outreach]]` | Use when composing personalized investor pitches, grant applications (IRI, ON Media), and follow-up investment communications. |
| `[[and_os/lib/skills/ios-game-builder/SKILL|ios-game-builder]]` | Use when prototyping, engineering, compiling, and debugging native iOS/macOS games and apps in Swift, SwiftUI, and SpriteKit without user programming. |
| `[[and_os/lib/skills/knowledge-promoter/SKILL|knowledge-promoter]]` | Primary closed-loop knowledge orchestrator for AnD os. Handles dual-direction memory: (1) Pre-flight Recall to retrieve established domain invariants  |
| `[[and_os/lib/skills/llm-council/SKILL|llm-council]]` | Use when orchestrating multi-agent consensus debates, adversarial evaluations, and multi-model synthesis on critical decisions. |
| `[[and_os/lib/skills/mattermost-sync/SKILL|mattermost-sync]]` | Use when synchronizing studio chat channels, compiling daily communication digests, and isolating cross-departmental blockers. |
| `[[and_os/lib/skills/meetings-hub/SKILL|meetings-hub]]` | Use when decomposing production meeting transcripts into prioritized action points with assignees and deadline milestones. |
| `[[and_os/lib/skills/negotiation/SKILL|negotiation]]` | Use when preparing for high-stakes business negotiations, difficult team conversations, client pitches, or contractual objections. |
| `[[and_os/lib/skills/obsidian-bases/SKILL|obsidian-bases]]` | Create, validate, and maintain Obsidian Bases (.base files) with views, reactive filters, formulas, and summaries. Use when generating database-like t |
| `[[and_os/lib/skills/openmontage-builder/SKILL|openmontage-builder]]` | Use when performing generative video assembly, timeline orchestration, reference-guided pacing cuts, and automated hardware-accelerated FFmpeg editing |
| `[[and_os/lib/skills/portfolio-summary/SKILL|portfolio-summary]]` | Use when analyzing personal multi-currency financial balances, investment brokerage assets, and monthly cashflow dynamics. |
| `[[and_os/lib/skills/postmortem-analyzer/SKILL|postmortem-analyzer]]` | Use when conducting sprint postmortems, isolating production bottlenecks via Theory of Constraints (TOC), and updating lessons learned. |
| `[[and_os/lib/skills/project-state/SKILL|project-state]]` | Use when capturing operational delta snapshots of active studio production projects, sprint velocity, and blocker states. |
| `[[and_os/lib/skills/prompt-improver/SKILL|prompt-improver]]` | Use when refining agent system prompts, clarifying underspecified user queries, and distilling high-fidelity context instructions. |
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
