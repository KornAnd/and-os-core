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

**Назначение:** единый источник истины по статусу каждого скилла. Заменяет необходимость держать lifecycle-поле в каждом отдельном SKILL.md (см. [[and_os/lib/skills/GOVERNANCE|GOVERNANCE.md]]).

**Статусы:** `ACTIVE` (используется) · `EXPERIMENTAL` (новый, не обкатан) · `REVIEW` (нужна проверка — устарел или не используется) · `DEPRECATED` (заменён/не нужен) · `ARCHIVED` (сохранён для истории)

**Регламент ревизии неактивности (Правило №18):** скиллы со статусом `REVIEW` или без использования >3 месяцев подлежат переработке, слиянию или архивации в декабре 2026.

---

## Системные и архитектурные (17)

| Skill | Status | Volatility | Note |
|---|---|---|---|
| sync-context | ACTIVE | STATIC | автоиндексация, безопасно |
| vault-router | ACTIVE | STATIC | маршрутизация новых файлов |
| goal-writer | REVIEW | STATIC | формулирование измеримых целей (Dormancy Review 2026-10) |
| project-state | REVIEW | STATIC | ключевой для Project State First (Dormancy Review 2026-10) |
| decision-log | ACTIVE | STATIC | фиксация решений |
| knowledge-promoter | ACTIVE | STATIC | кристаллизация знаний |
| context-compressor | ACTIVE | STATIC | сжатие контекста |
| skill-router | ACTIVE | STATIC | выбор primary skill |
| skill-creator | ACTIVE | STATIC | создание и валидация новых скиллов по спецификации |
| task-graph | ACTIVE | STATIC | оркестрация графа задач (DAG) и распараллеливание |
| system-audit | ACTIVE | STATIC | аудит и телеметрия |
| system-architect | ACTIVE | STATIC | архитектурный бутстрап систем, Spec-Before-Code, C4/ADR |
| clean-code-guardian | ACTIVE | STATIC | инженерный стандарт чистого кода Uncle Bob / AnD os |
| obsidian-bases | ACTIVE | STATIC | декларативные базы и реактивные таблицы Obsidian .base |
| external-skills-gateway | ACTIVE | STATIC | суверенный шлюз поиска и инспекции внешних агентских скиллов |
| github-ops | ACTIVE | STATIC | токеноэффективная работа с GitHub через официальный CLI (gh) |
| dev-flow | ACTIVE | STATIC | модульный конвейер строгой разработки и Stop-on-3 |
| app-deconstructor | ACTIVE | STATIC | статический реверс-инжиниринг и декомпозиция архитектуры |

## Мета (2)

| Skill | Status | Volatility | Note |
|---|---|---|---|
| prompt-improver | REVIEW | SEMI-STABLE | улучшение промптов (Dormancy Review 2026-10) |
| llm-council | ACTIVE | STATIC | совет 5 ролей с запретами, стресс-тест решений |

## Продакшн и команда (6)

| Skill | Status | Volatility | Note |
|---|---|---|---|
| status-report | ACTIVE | STATIC | отчёты по проектам |
| meetings-hub | ACTIVE | STATIC | встречи и протоколы |
| employee-hub | ACTIVE | STATIC | сотрудники и фидбек |
| budget-calculator | REVIEW | SEMI-STABLE | ставки и сметы (Dormancy Review 2026-10) |
| ftrack-sync | ACTIVE | VOLATILE | зависит от API/экспорта Ftrack |
| mattermost-sync | ACTIVE | VOLATILE | синхронизация тредов и сообщений Mattermost |
| postmortem-analyzer | ACTIVE | STATIC | ретроспективы спринтов, TOC-анализ и поиск узких мест производства |

## Контент и коммуникации (7)

| Skill | Status | Volatility | Note |
|---|---|---|---|
| cg-article | ACTIVE | STATIC | статьи VK CG_core и перевод для LinkedIn |
| cg-content-factory | ACTIVE | SEMI-STABLE | мультипостинг контент-фабрика (VK, Сетка, LinkedIn, 3D обложка) |
| cg-core-consulting | ACTIVE | STATIC | аудит студий и консалтинг |
| story-dev | ACTIVE | STATIC | разработка сценариев |
| script-bible-extractor | ACTIVE | STATIC | экстракция библии проекта, карточек персонажей и локаций |
| investor-outreach | ACTIVE | SEMI-STABLE | питчи и письма |
| clipping-finder | ACTIVE | STATIC | поиск по базе знаний Clippings |
| yt-analyze | REVIEW | VOLATILE | парсинг транскриптов YouTube (Dormancy Review 2026-10) |

## AI-инструменты (4)

| Skill | Status | Volatility | Note |
|---|---|---|---|
| ai-rule | ACTIVE | VOLATILE | правила генерации и модели (Wan/LTX/SDXL) |
| higgsfield-seedance-prompt | ACTIVE | VOLATILE | генерация видеопромптов Seedance |
| comfy-builder | ACTIVE | STATIC | сборка, визуализация, валидация и отладка графов ComfyUI |
| openmontage-builder | ACTIVE | SEMI-STABLE | агентская видеостудия монтажа по сценарию/референсу |

## Книги и знания (3)

| Skill | Status | Volatility | Note |
|---|---|---|---|
| book-hub | ACTIVE | STATIC | конспекты и саммари книг |
| book-summary-practical | ACTIVE | STATIC | прикладные управленческие саммари (тест понедельника, алгоритмы действий) |
| teach-hub | REVIEW | STATIC | пошаговая интерактивная учебная система навыков (Dormancy Review 2026-10) |

## Личное и стратегия (5)

| Skill | Status | Volatility | Note |
|---|---|---|---|
| portfolio-summary | ACTIVE | SEMI-STABLE | брокерские отчёты РФ (БКС, Альфа) |
| tax-compliance | ACTIVE | VOLATILE | налоги (НПД/ИП) |
| strategy-review | REVIEW | SEMI-STABLE | аудит 25 целей и портфеля P1-P5 (Dormancy Review 2026-10) |
| career-radar | ACTIVE | SEMI-STABLE | радар вакансий и скоринг рынка для System Architect |
| executive-mirror | ACTIVE | STATIC | ежемесячная 360° ретроспектива и стратегическая калибровка |

## Здоровье и семья (5)

| Skill | Status | Volatility | Note |
|---|---|---|---|
| telemetry_sync | ACTIVE | VOLATILE | синхронизация биометрии telemetry_sync |
| uc-diet-planning | ACTIVE | SEMI-STABLE | протокол диеты при chronic_condition |
| endurance-training-plan | ACTIVE | SEMI-STABLE | план подготовки к Half Ironman 70.3 |
| health-diagnostics-hub | ACTIVE | SEMI-STABLE | комплексный хаб семейного здоровья |
| health-orchestrator | ACTIVE | STATIC | кросс-синтез клиники, биометрии telemetry_sync и спортивных нагрузок |

## Ta-Bu и переговоры (2)

| Skill | Status | Volatility | Note |
|---|---|---|---|
| ta-bu-plan | REVIEW | SEMI-STABLE | стратегический план развития Ta-Bu (Dormancy Review 2026-10) |
| negotiation | REVIEW | STATIC | стратегические переговоры (Dormancy Review 2026-10) |

## Инструменты и документы (6)

| Skill | Status | Volatility | Note |
|---|---|---|---|
| weeek-hub | ACTIVE | VOLATILE | синхронизация и аналитика задач Weeek |
| document-hub | ACTIVE | STATIC | универсальный конвертер (MarkItDown) и хаб документов |
| app-bridge | REVIEW | STATIC | связывание Obsidian и внешних веб-проектов (React/Python/API) (Dormancy Review 2026-10) |
| ui-inspector | ACTIVE | STATIC | инспекция и Component Map UI/Dash/HTML компонентов |
| board-analyzer | ACTIVE | STATIC | анализ интерактивных досок (Ххолст, Miro, Excalidraw) |
| cg-pipeline | ACTIVE | STATIC | мульти-DCC гибридный 3D-пайплайн (cg_core.py, Blender/Houdini) |
| api-contract-generator | ACTIVE | STATIC | генератор строгих OperationSpec контрактов и схем данных |
| hybrid-animatic-director | ACTIVE | STATIC | сборка шотных анимитиков и хронометража по сценарию |
| hybrid-comfyui-render | ACTIVE | STATIC | гибридная 3D-to-AI стилизация через Multi-ControlNet пассы |
| temporal-consistency-guard | ACTIVE | STATIC | контроль темпоральной стабильности и дефликеринг нейро-анимации |
| editorial-otio-conform | ACTIVE | STATIC | конформ монтажных таймлайнов, OpenTimelineIO и сборка шотов |

## Gamedev и интерактив (1)

| Skill | Status | Volatility | Note |
|---|---|---|---|
| ios-game-builder | ACTIVE | STATIC | разработка нативных 2D/3D игр на Swift/SpriteKit (Island 9) |

---

## Устаревшие и депрецированные скиллы (9)

| Skill | Status | Reason | Replacement |
|---|---|---|---|
| diary-review | DEPRECATED | Каталог Diary выведен в архив | strategy-review |
| spreadsheet-analyzer | DEPRECATED | Объединён в универсальный хаб | document-hub (convert_doc.py / xl_analyze.py) |
| image-ocr | DEPRECATED | Объединён в универсальный хаб | document-hub (convert_doc.py / doc_analyze.py) |
| lab-analyzer | DEPRECATED | Интегрирован в семейный хаб | health-diagnostics-hub |
| med-protocol-compatibility | DEPRECATED | Интегрирован в семейный хаб | health-diagnostics-hub |
| article-translator | DEPRECATED | Объединён в скилл cg-content-factory (v2.0) | cg-content-factory |
| cg-article | DEPRECATED | Объединён в мультиплатформенную фабрику | cg-content-factory (v2.0) |
| telemetry_sync | DEPRECATED | Выгрузка интегрирована в хаб здоровья | health-diagnostics-hub (telemetry_sync_sync.py) |
| comfyui | DEPRECATED | Объединён в скилл ai-rule (Режим 2) | ai-rule |

---
[[CONTEXT|← Наверх]]
