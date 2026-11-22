# 🧭 AnD os Skills Catalog & Discovery Matrix
### Complete Catalog of Production-Grade Agentic Skills

[English](SKILLS_CATALOG.md) | [Русская версия](#-каталог-системных-навыков-and-os-на-русском)

The **AnD os Microkernel** ships with 12 canonical, production-tested skills adhering to **Skill Module ABI v2.1**. Each skill is declarative, hermetically probed in $<300$ ms, and engineered to eliminate context bloat and hallucinated agent execution.

---

## 📋 Catalog Summary

| Skill | Modality | Primary Trigger | Core Innovation |
| :--- | :---: | :--- | :--- |
| **[`system-architect`](#1-system-architect)** | Declarative | Designing new services, games, or pipelines | **Phase -1 Grilling Gate**: 6 calibrating frontier questions before drafting architecture. |
| **[`task-graph`](#2-task-graph)** | Declarative | Multi-file or multi-step engineering tasks | **to-tickets & DAG**: Vertical-slice tracer bullets with file-contention locking. |
| **[`dev-flow`](#3-dev-flow)** | Executable | Feature development, bug fixing, refactoring | **Red-Loop-First & Uncle Bob Clean**: Zero changes allowed without reproducing tests. |
| **[`system-audit`](#4-system-audit)** | Executable | Health audits, security scans, test reviews | **Test Value Bar & Retirement Cards**: Mutational proof of real test value. |
| **[`memory`](#5-memory)** | Executable | Recording lessons learned, retrieving traps, ADRs | **Closed-Loop Memory**: Pre-flight recall (<15ms) and post-flight learning. |
| **[`file-lifecycle`](#6-file-lifecycle)** | Executable | Note classification, routing, and index sync | **Dual-Speed Governance**: M1 semantic routing + M2 automated index synchronization. |
| **[`temporal-consistency-guard`](#7-temporal-consistency-guard)** | Executable | AI animation, video rendering, deflicker QA | **Hyperframes Contract**: Deterministic frame-by-frame variance & drift validation. |
| **[`skill-creator`](#8-skill-creator)** | Executable | Creating, testing, and dieting agent skills | **ABI v2.1 Validator**: Strict frontmatter schema, A/B prompt testing, and diet gates. |
| **[`skill-router`](#9-skill-router)** | Declarative | Multi-domain requests, intent arbitration | **Rule #12 (One Primary Skill)**: Eliminates routing ambiguity and tool sprawl. |
| **[`context-compressor`](#10-context-compressor)** | Declarative | Inspecting large repositories or directories | **Think in Code Bundling**: Filters output on host to return $<100$ tokens of essence. |
| **[`github-ops`](#11-github-ops)** | Declarative | Managing issues, PRs, and public releases | **Zero-Leak Release Protocol**: Mathematical air-gap isolation and token-efficient jq recipes. |
| **[`obsidian-bases`](#12-obsidian-bases)** | Declarative | Tabular data representation in Markdown | **Native Bases (.base)**: Reactive views and formulas without heavy JS plugins. |

---

## 🛠️ Detailed Skill Specifications

### 1. `system-architect`
- **Version:** `1.2.0` | **Domain:** `system`
- **Trigger:** When bootstrapping new software architectures, web services, or 3D pipelines.
- **Key Protocol:** Strictly enforces **Phase -1 Grilling Gate** (adapted from Matt Pocock & gstack). The agent asks exactly 6 frontier questions with explicit recommendations before drafting any code or C4 diagrams.
- **Canary Probe:** `python3 and_os/bin/architect_engine.py list`

### 2. `task-graph`
- **Version:** `1.3.0` | **Domain:** `system`
- **Trigger:** When planning tasks spanning $>3$ files or needing parallel agent dispatch.
- **Key Protocol:** Converts user briefs into a Directed Acyclic Graph (DAG) with **to-tickets** vertical tracer-bullet slicing. Automatically audits file contention (`MUTUAL_EXCLUSION_REQUIRED`) to prevent subagents from editing the same file in parallel.
- **Canary Probe:** `python3 and_os/bin/task_db_engine.py --help`

### 3. `dev-flow`
- **Version:** `2.0.0` | **Domain:** `system`
- **Trigger:** When fixing defects, refactoring, or authoring production code.
- **Key Protocol:** Enforces the **TDD Iron Law** and **Red-Loop-First** protocol (obra/superpowers). Prohibits modifying production code until an isolated, failing test reproduces the defect. Integrates Uncle Bob Clean Code gates (zero bare excepts, max nesting $\le 4$).
- **Canary Probe:** `test -d and_os/lib/skills/dev-flow`

### 4. `system-audit`
- **Version:** `2.0.0` | **Domain:** `system`
- **Trigger:** When verifying system health, audit logs, or deprecating test suites.
- **Key Protocol:** 8-ring Health Grid validation + **4-Question Test Value Bar**. A test is only kept if removing it causes an observable regression. Decommissioning a test requires a formal **Retirement Card**. Includes OWASP/STRIDE security scans.
- **Canary Probe:** `python3 and_os/bin/sys_cli.py audit --help`

### 5. `memory`
- **Version:** `2.0.0` | **Domain:** `knowledge`
- **Trigger:** Pre-flight recall of known traps or post-flight crystallization of fixes.
- **Key Protocol:** 4 deterministic modes: `M1 recall` (in-memory search), `M2 learn` (`sys_cli learn`), `M3 manage` (periodic pruning), and `M4 ADR` (Architecture Decision Records).
- **Canary Probe:** `python3 and_os/bin/sys_cli.py find 'knowledge'`

### 6. `file-lifecycle`
- **Version:** `2.0.0` | **Domain:** `system`
- **Trigger:** Classifying and persisting new documents, or updating file maps.
- **Key Protocol:** `M1 Route` directs notes to their canonical island; `M2 Index` keeps wikilinks, tags, and `CONTEXT.md` in sync with 0% orphan files.
- **Canary Probe:** `python3 and_os/bin/context_router.py --help`

### 7. `temporal-consistency-guard`
- **Version:** `1.1.0` | **Domain:** `ai`
- **Trigger:** Verifying visual and lighting continuity across AI video shots.
- **Key Protocol:** Enforces deterministic render contracts (`render_contract.schema.json`) inspired by heygen/hyperframes. Calculates luminance variance, pixel drift, and flags optical flickering.
- **Canary Probe:** `test -d and_os/lib/skills/temporal-consistency-guard`

### 8. `skill-creator`
- **Version:** `1.2.0` | **Domain:** `system`
- **Trigger:** Creating or updating agent skills.
- **Key Protocol:** Validates YAML frontmatter, enforces hermetic `<300ms` canary probes, runs A/B prompt evaluation, and manages description token diet.
- **Canary Probe:** `python3 and_os/lib/skills/skill-creator/scripts/validate_skill.py and_os/lib/skills/skill-creator`

### 9. `skill-router`
- **Version:** `1.0.0` | **Domain:** `system`
- **Trigger:** Arbitrating which skill to use when requests overlap.
- **Key Protocol:** Enforces **Rule #12 (One Primary Skill)**: Exactly one primary skill is active at any time, eliminating tool sprawl and conflicting instructions.
- **Canary Probe:** `test -f and_os/lib/skills/ROUTING.md`

### 10. `context-compressor`
- **Version:** `1.0.0` | **Domain:** `system`
- **Trigger:** When processing large directories, long logs, or multi-turn sessions.
- **Key Protocol:** Generates deterministic subshell scripts to summarize files on the host, returning $\le 50$ tokens of pure answer (up to 98.8% token savings).
- **Canary Probe:** `python3 and_os/bin/context_bundler.py --help`

### 11. `github-ops`
- **Version:** `1.3.0` | **Domain:** `engineering`
- **Trigger:** GitHub PR triage, issue inspection, or open-source repository exports.
- **Key Protocol:** Uses token-efficient `gh` CLI commands filtered with `--jq`. Implements the **Zero-Leak Release Protocol** to mathematically isolate private workstation data during release.
- **Canary Probe:** `test -x /opt/homebrew/bin/gh || which gh`

### 12. `obsidian-bases`
- **Version:** `1.0.0` | **Domain:** `system`
- **Trigger:** Defining tabular views, formulas, and reactive summaries in Markdown.
- **Key Protocol:** Standardizes declarative `.base` files over YAML frontmatter properties without requiring heavy third-party JavaScript engines.
- **Canary Probe:** `test -d and_os/lib/skills/obsidian-bases`

---

<br/>

## 🇷🇺 Каталог системных навыков AnD os (на русском)

Микроядро **AnD os** поставляется с 12 каноническими навыками разработки, сертифицированными по стандарту **ABI v2.1**. Они предотвращают деградацию контекста модели, ликвидируют галлюцинации и гарантируют детерминированное выполнение кода.

### Краткий функциональный гид:

1. **`system-architect` (v1.2):** Архитектурный предпроектный допрос (*Phase -1 Grilling*). Агент задает строго 6 калибрующих вопросов с готовыми рекомендациями до того, как создаст первый файл спецификации или кода.
2. **`task-graph` (v1.3):** Превращение больших задач в ориентированный ациклический граф (DAG) и вертикальные срезы тикетов (*to-tickets / tracer-bullets*). Защищает параллельных агентов от редактирования одних и тех же файлов (`MUTUAL_EXCLUSION_REQUIRED`).
3. **`dev-flow` (v2.0):** Железный закон TDD и протокол *Red-Loop-First*. Запрещено трогать рабочий код, пока сбой не воспроизведён в минимальном изолированном тесте. Интегрирует стандарт чистого кода Мартина (Uncle Bob).
4. **`system-audit` (v2.0):** 8-кольцевой аудит здоровья ядра Health Grid + 4-вопросный *Test Value Bar*. Тест сохраняется только при наличии мутационного доказательства его пользы; при удалении оформляется карточка *Retirement Card*.
5. **`memory` (v2.0):** Замкнутый контур самообучения (Pre-flight Recall ловушек за $<15$ мс и Post-flight Learn решений) + реестр архитектурных решений ADR.
6. **`file-lifecycle` (v2.0):** Маршрутизация новых заметок в целевые каталоги и мгновенная синхронизация карт `CONTEXT.md` (0% потерянных файлов).
7. **`temporal-consistency-guard` (v1.1):** Контроль дефликеринга и детерминированные рендер-контракты покадровой валидации видео против референса.
8. **`skill-creator` (v1.2):** Создание, линтинг и тестирование новых навыков агента по стандарту ABI v2.1 с контролем токенов.
9. **`skill-router` (v1.0):** Арбитраж вызовов — жесткий выбор ровно одного ведущего навыка (Правило №12) для защиты от распыления внимания агента.
10. **`context-compressor` (v1.0):** Сжатие контекста по парадигме *Think in Code* — выполнение локальных фильтров на хосте с возвратом в чат только результата ($<100$ токенов).
11. **`github-ops` (v1.3):** Токеноэффективная работа с GitHub через CLI и математический протокол безопасного экспорта *Zero-Leak*.
12. **`obsidian-bases` (v1.0):** Создание декларативных реактивных таблиц `.base` над Markdown-заметками без тяжелых плагинов.

---
[[Vault|← Vault]]
