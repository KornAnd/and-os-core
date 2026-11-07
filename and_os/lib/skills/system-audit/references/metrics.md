---
tags:
  - nero
  - skills
  - system
  - audit
  - метрики
---

# Метрики эффективности skill-системы

Референс для `system-audit` (Performance Audit). Источники данных: `and_os/lib/skills/telemetry.md`, записи `decision-log`, записи `knowledge-promoter`, снимки `project-state`.

## Принцип измерения

Мерим только то, что **уже фиксируется** существующими артефактами или одной строкой в telemetry. Не создаём отчётности на каждый QUICK-запрос — это само по себе тратит токены. Если данных мало/нет — вывод помечается как `architectural`, а не статистический.

## 7 метрик

| # | Метрика | Формула | Источник | Цель |
|---|---------|---------|----------|------|
| 1 | **First-pass success** | задачи без rework ÷ все задачи | telemetry `rework=0` | ≥ 70% |
| 2 | **Routing accuracy** | задачи с верным primary ÷ все задачи | telemetry `route=ok` | ≥ 90% |
| 3 | **Context efficiency** | задачи с адекватным контекстом (min/work/compressed без перерасхода) ÷ задачи WORK+ | telemetry `ctx=min/work/compressed` | ≥ 80% |
| 4 | **Knowledge reuse rate** | задачи, решённые существующим знанием ÷ все задачи | telemetry `result=reused` | ≥ 40% |
| 5 | **Knowledge promotion rate** | промотированные L2+ ÷ значимые завершённые задачи | записи `knowledge-promoter` | рост от 0 |
| 6 | **Decision reuse** | доля ACTIVE решений без повторного обсуждения | `decision-log` (ACTIVE vs SUPERSEDED) | — |
| 7 | **Avg iterations** | Σ итераций ÷ число задач | telemetry `iter` | ≤ 1.5 |
| 8 | **Context cost** | Σ загруженного контекста (фрагменты/токены) на задачу | telemetry `ctx` + фактическая загрузка | снижение |
| 9 | **Version drift** | скиллы, где `lifecycle`/`ttl`/`version`/`reviewed` не обновлены ÷ все скиллы | frontmatter SKILL.md при `system-audit` | ≈ 0 |
| 10 | **Duplicate rate** | дубли/пересечения скиллов и знаний, требующие REVIEW | registry + аудит | снижение |
| 11 | **Target Mix (Domain/System)** | доля прикладных задач (WORK + STRATEGIC) ÷ все задачи | telemetry `MODE=WORK/STRAT` | ≥ 60% |

## Формат строки telemetry

Одна строка на значимую задачу (WORK / STRATEGIC / SYSTEM, **НЕ QUICK**), добавляется после завершения:

```text
- YYYY-MM-DD | MODE | skill | тема/проект | route(ok|manual) | ctx(min|work|full|compressed) | iter | rework(0|n) | result(new|reused) | K(+|-) | D(+|-)
```

- `ctx=min` — точечный контекст (<10 фрагментов / <5k токенов).
- `ctx=work` — рабочий контекст задачи (10–25 фрагментов / 5–20k токенов).
- `ctx=full` — тяжелый анализ (>25 фрагментов / >20k токенов).
- `ctx=compressed` — сжато скриптом (Think in Code) или context-compressor.
- `K(+)` — знание промотировано (`knowledge-promoter` сработал), `K(-)` — нет.
- `D(+)` — решение зафиксировано (`decision-log` сработал), `D(-)` — нет.

## Как читать

1. **Пустой/малый telemetry** → вывод `architectural`, не подменяй числами.
2. **Тренды важнее абсолютов** — сравнивай периоды (месяц к месяцу).
3. **Не штрафуй за K(-)/D(-)** — не каждая задача должна давать знание или решение; важен только тренд метрик #5 и #6.

---
[[|[[CONTEXT|← Наверх]]