---
tags:
  - nero
  - skills
  - system
  - registry
sticker: ""
color: ""
---

# REGISTRY.md — Unified Skill Registry

**Назначение:** единый источник истины (SSoT) по статусу каждого скилла. Поле `lifecycle` в frontmatter SKILL.md — проекция реестра (хранится для совместимости, синхронизация контролируется drift-проверкой, см. [[and_os/lib/skills/GOVERNANCE|GOVERNANCE.md]]).

**Статусы:** `ACTIVE` (используется) · `EXPERIMENTAL` (новый, не обкатан) · `REVIEW` (нужна проверка — устарел или не используется) · `DEPRECATED` (заменён/не нужен) · `ARCHIVED` (сохранён для истории)

**Регламент ревизии неактивности (Правило №18):** скиллы со статусом `REVIEW` или без использования >3 месяцев подлежат переработке, слиянию или архивации в декабре 2026.

---

## Системные и архитектурные (12)

| Skill | Status | Volatility | Note |
|---|---|---|---|
| context-compressor | ACTIVE | STATIC | сжатие контекста |
| skill-router | ACTIVE | STATIC | выбор primary skill |
| skill-creator | ACTIVE | STATIC | создание и валидация новых скиллов по спецификации |
| memory | ACTIVE | STATIC | замкнутый контур памяти: recall / learn / manage + ADR (C11: knowledge-promoter + decision-log, v2.0) |
| file-lifecycle | ACTIVE | STATIC | классификация, маршрутизация заметок и синхронизация CONTEXT.md (C11: sync-context + vault-router, v2.0) |
| task-graph | ACTIVE | STATIC | оркестрация DAG, tracer-bullet нарезка тикетов (to-tickets) и взаимное исключение |
| system-audit | ACTIVE | STATIC | аудит ядра, телеметрия, Test Value Bar, Retirement Cards + security-линза (C11: security-audit absorbed, v2.0) |
| system-architect | ACTIVE | STATIC | архитектурный бутстрап систем, Spec-Before-Code, Phase -1 Grilling/Interview |
| obsidian-bases | ACTIVE | STATIC | декларативные базы и реактивные таблицы Obsidian .base |
| external-skills-gateway | ACTIVE | STATIC | суверенный шлюз поиска и инспекции внешних агентских скиллов |
| github-ops | ACTIVE | STATIC | токеноэффективная работа с GitHub через официальный CLI (gh) |
| dev-flow | ACTIVE | STATIC | конвейер TDD Iron Law, Red-Loop-First, Stop-on-3 + инженерный стандарт Uncle Bob (C11: clean-code-guardian absorbed, v2.0) |

## Мета (2)

| Skill | Status | Volatility | Note |
|---|---|---|---|
| prompt-improver | ACTIVE | SEMI-STABLE | адаптация рукописных/диктованных промптов в 5-блочную спецификацию (C10: re-anchored, woken) |
| llm-council | ACTIVE | STATIC | совет 5 ролей с запретами, стресс-тест решений |

## Продакшн и команда (5)

| Skill | Status | Volatility | Note |
|---|---|---|---|
| status-report | ACTIVE | STATIC | отчёты по проектам: снапшот состояния, producer brief, ftrack, полный аудит, TOC-ретро (объединение project-state + postmortem-analyzer) |
| meetings-hub | ACTIVE | STATIC | встречи и протоколы |
| employee-hub | ACTIVE | STATIC | сотрудники и фидбек |
| ftrack-sync | ACTIVE | VOLATILE | зависит от API/экспорта Ftrack |
| mattermost-sync | ACTIVE | VOLATILE | синхронизация тредов и сообщений Mattermost |

## Контент и коммуникации (5)

| Skill | Status | Volatility | Note |
|---|---|---|---|
| cg-content | ACTIVE | STATIC | весь контент CG_core: статьи RU VK/Сетка + EN LinkedIn, slop-аудит, батч-пайплайн с обложкой (C11: cg-article + cg-content-factory, v2.0) |
| cg-core-consulting | ACTIVE | STATIC | аудит студий и консалтинг |
| story-dev | ACTIVE | STATIC | сценарии + экстракция библии проекта, карточек персонажей и локаций (C11: script-bible-extractor absorbed, v2.0, движок sys_cli bible) |
| investor-outreach | ACTIVE | SEMI-STABLE | питчи и письма |
| clipping-finder | ACTIVE | STATIC | поиск по базе знаний Clippings |

## AI-инструменты (4)

| Skill | Status | Volatility | Note |
|---|---|---|---|
| ai-rule | ACTIVE | VOLATILE | правила генерации и модели (Wan/LTX/SDXL) |
| higgsfield-seedance-prompt | ACTIVE | VOLATILE | генерация видеопромптов Seedance |
| comfy-studio | ACTIVE | STATIC | сборка, визуализация, валидация графов ComfyUI + мультипасный 3D-to-AI рендер (C11: hybrid-comfyui-render absorbed, v2.0) |
| openmontage-builder | ACTIVE | SEMI-STABLE | агентская видеостудия монтажа по сценарию/референсу |

## Книги и знания (3)

| Skill | Status | Volatility | Note |
|---|---|---|---|
| deep-research | ACTIVE | STATIC | глубокий мультиисточниковый ресёрч: outline → parallel deep (subagents ≤3) → integrity-гейт с locator-цитатами → RU-отчёт в Clippings |
| book-pipeline | ACTIVE | STATIC | книжный конвейер: 8-блок саммари, прикладные decision-toolkit (тест понедельника), 5-акт структура рукописей (объединение book-hub + book-summary-practical) |
| teach-hub | ACTIVE | STATIC | обучение сотрудников студии, менторство, B2B образовательный консалтинг (C10: re-anchored, Island 2 CG_core) |

## Личное и стратегия (4)

| Skill | Status | Volatility | Note |
|---|---|---|---|
| portfolio-summary | ACTIVE | SEMI-STABLE | брокерские отчёты РФ (БКС, Альфа) |
| tax-compliance | ACTIVE | VOLATILE | налоги (НПД/ИП) |
| goal-system | ACTIVE | SEMI-STABLE | полный цикл целей: M1 постановка + M2 аудит достижения + M3 /goal + M4 ежемесячная 360° ретроспектива (C10/C11: goal-writer, strategy-review, executive-mirror, v2.0) |
| career-radar | ACTIVE | SEMI-STABLE | радар вакансий и скоринг рынка для System Architect |

## Здоровье и семья (3)

| Skill | Status | Volatility | Note |
|---|---|---|---|
| uc-diet-planning | ACTIVE | SEMI-STABLE | протокол диеты при chronic_condition |
| health-hub | ACTIVE | SEMI-STABLE | семейный хаб здоровья: диагностика (full/lab/protocol) + кросс-синтез с telemetry_sync/InBody (C11: health-diagnostics-hub + health-orchestrator, v2.0) |
| training-hub | ACTIVE | SEMI-STABLE | замкнутый атлетический контур: еженедельная telemetry_sync-телеметрия (M1) + периодизация Half Ironman под медицинский гейт (C11: telemetry_sync + endurance-training-plan, v2.0) |

## Ta-Bu и переговоры (2)

| Skill | Status | Volatility | Note |
|---|---|---|---|
| ta-bu-plan | ACTIVE | SEMI-STABLE | стратегия Ta-Bu + ценообразование проектов, Режим 4 (C10: budget-calculator absorbed, v2.0) |
| negotiation | ACTIVE | STATIC | плагин 4 доменов: коммерция, интервью (обе стороны), увольнения, сложный фидбек (C10: v2.0) |

## Инструменты и документы (10)

| Skill | Status | Volatility | Note |
|---|---|---|---|
| weeek-hub | ACTIVE | VOLATILE | синхронизация и аналитика задач Weeek |
| reverse-engineer-anything | ACTIVE | STATIC | REA: бинарный инспект/декомпиляция + C4-декомпозиция чужих кодобаз и сервисов (объединение app-deconstructor) |
| document-hub | ACTIVE | STATIC | универсальный конвертер (MarkItDown) и хаб документов |
| ui-inspector | ACTIVE | STATIC | инспекция и Component Map UI/Dash/HTML компонентов |
| board-analyzer | ACTIVE | STATIC | анализ интерактивных досок (Ххолст, Miro, Excalidraw) |
| cg-pipeline | ACTIVE | STATIC | мульти-DCC гибридный 3D-пайплайн (cg_core.py, Blender/Houdini) |
| api-contract-generator | ACTIVE | STATIC | генератор строгих OperationSpec контрактов и схем данных |
| cut-suite | ACTIVE | STATIC | аниматики + editorial-конформ: таймлайны, OTIO/EDL/XML, хэндлы (C11: hybrid-animatic-director + editorial-otio-conform, v2.0) |
| temporal-consistency-guard | ACTIVE | STATIC | контроль стабильности, дефликеринг и детерминированные рендер-контракты |
| houdini-bridge | ACTIVE | STATIC | управление запущенным Houdini 22.x через MCP-мост fxhoudinimcp: scene-билд, frame cook, viewport-capture, sanitized payload |

## Gamedev и интерактив (1)

| Skill | Status | Volatility | Note |
|---|---|---|---|
| ios-game-builder | ACTIVE | STATIC | разработка нативных 2D/3D игр на Swift/SpriteKit (Island 9) |

---

## Устаревшие и депрецированные скиллы (34)

| Skill | Status | Reason | Replacement |
|---|---|---|---|
| book-hub | DEPRECATED | Слияние C7: единый книжный конвейер | book-pipeline |
| book-summary-practical | DEPRECATED | Слияние C7: единый книжный конвейер | book-pipeline |
| project-state | DEPRECATED | Слияние C7: режим Operational Snapshot | status-report |
| postmortem-analyzer | DEPRECATED | Слияние C7: режим TOC Retro | status-report |
| app-deconstructor | DEPRECATED | Слияние C7: Class B (кодобазы и сервисы) | reverse-engineer-anything |
| diary-review | DEPRECATED | Каталог Diary выведен в архив | strategy-review |
| spreadsheet-analyzer | DEPRECATED | Объединён в универсальный хаб | document-hub (convert_doc.py / xl_analyze.py) |
| image-ocr | DEPRECATED | Объединён в универсальный хаб | document-hub (convert_doc.py / doc_analyze.py) |
| lab-analyzer | DEPRECATED | Интегрирован в семейный хаб | health-diagnostics-hub |
| med-protocol-compatibility | DEPRECATED | Интегрирован в семейный хаб | health-diagnostics-hub |
| article-translator | DEPRECATED | Объединён в скилл cg-content-factory | cg-content-factory |
| comfyui | DEPRECATED | Объединён в скилл ai-rule (Режим 2) | ai-rule |
| app-bridge | ARCHIVED | Архив C10: функционал в диспетчере `sys_cli app`/`project` + фоновые синки `sys_cli sync`; спецификация PROJECT.md → `dev-flow/references/PROJECT_SPEC.md` | sys_cli (app/project) + dev-flow |
| budget-calculator | DEPRECATED | Слияние C10: режим 4 «Проектное ценообразование» (ставки, множители, ведомости, budget_calc.py) | ta-bu-plan |
| goal-writer | DEPRECATED | Слияние C10: режим M3 «/goal Engineering» + M1 постановка | goal-system |
| strategy-review | DEPRECATED | Слияние C10: режим M2 «Achievement Audit» (25 целей, P1-P5, review_YYYY-MM.md) | goal-system |
| yt-analyze | ARCHIVED | Архив C10b: 0 использования с осени (Dormancy Review 2026-10); движок `yt_analyze.py` остаётся в фасаде `sys_cli tools yt-analyze` | sys_cli tools yt-analyze |
| cg-article | DEPRECATED | Слияние C11: переименован в cg-content, контент-фабрика поглощена (режим M4) | cg-content |
| cg-content-factory | DEPRECATED | Слияние C11: батч-пайплайн стал режимом M4 | cg-content |
| script-bible-extractor | DEPRECATED | Слияние C11: Step 7 «Bible Extraction» (движок sys_cli bible) | story-dev |
| hybrid-comfyui-render | DEPRECATED | Слияние C11: режим M2 «Multi-Pass 3D→AI Render» (движок sys_cli hybrid-render) | comfy-studio |
| hybrid-animatic-director | DEPRECATED | Слияние C11: режим M1 «Animatic Assembly» (движок sys_cli animatic) | cut-suite |
| editorial-otio-conform | DEPRECATED | Слияние C11: режим M2 «Editorial Conform» (движок sys_cli conform) | cut-suite |
| clean-code-guardian | DEPRECATED | Слияние C11: инженерный стандарт стал §4 критериев dev-flow | dev-flow |
| security-audit | DEPRECATED | Слияние C11: security-линза стала режимом M2 (security_scan.py + STRIDE/OWASP/AST10) | system-audit |
| knowledge-promoter | DEPRECATED | Слияние C11: переименован в memory (M1 recall / M2 learn / M3 manage) | memory |
| decision-log | DEPRECATED | Слияние C11: режим M4 «ADR Decision Records» | memory |
| sync-context | DEPRECATED | Слияние C11: режим M2 «Index» (движок sync_context.py, алиас sys_cli sync) | file-lifecycle |
| vault-router | DEPRECATED | Слияние C11: режим M1 «Route» (движок context_router.py) | file-lifecycle |
| executive-mirror | DEPRECATED | Слияние C11: режим M4 «Monthly 360° Retrospective» (движок sys_cli tools mirror) | goal-system |
| health-orchestrator | DEPRECATED | Слияние C11: режим M4 «Cross-Domain Synthesis» (движок sys_cli health) | health-hub |
| health-diagnostics-hub | DEPRECATED | Слияние C11: переименован в health-hub (M1–M3 диагностика) | health-hub |
| endurance-training-plan | DEPRECATED | Слияние C11: режим M2 «Periodized Training Plan» | training-hub |
| telemetry_sync | DEPRECATED | Слияние C11: переименован в training-hub (M1 еженедельная биометрия) | training-hub |

---
[[and_os/lib/skills/CONTEXT|← Наверх]]
