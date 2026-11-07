---
tags:
  - nero
  - skills
  - knowledge
  - system
  - принципы
---

## KNOWLEDGE — Принципы эффективной системы знаний для LLM-агента

**Level:** L3
**Priority:** CORE
**Type:** PRINCIPLE
**Confidence:** high

**Result / evidence:** Полный аудит системы 28.08.2026 (14 записей telemetry). Подтверждено метриками: context efficiency 93% (ctx=min), first-pass success 93%, avg iterations 1.07, knowledge reuse 43%. Два контура были формальными: lifecycle 0/39 → операционализирован 39/39; scheduler существовал, но 0 джоб → создана ежемесячная джоба аудита.

**Insight:** Система становится эффективной не от количества функций, а от (а) дешевизны контекста, (б) встроенной измеримости, (в) операционализированного жизненного цикла. Формальный контур (есть стандарт, нет применения) хуже отсутствующего — он создаёт иллюзию управления и ложную уверенность.

**Principle or method:**
1. **Дешевизна контекста важнее функциональности.** One Primary Skill + поток Retrieval → Context → Execution → Memory + Context Budget + Don't Load Rule. Больше правил загрузки = дешевле каждая задача.
2. **Измеримость встроена в работу, а не добавлена сверху.** Одна обязательная строка telemetry после каждой WORK/STRATEGIC/SYSTEM-задачи; колонки K/D — дешёвые индикаторы knowledge loop. Не создавать отчётность ради отчётности.
3. **Жизненный цикл операционализируется, а не декларируется.** `lifecycle/ttl/version/reviewed` в frontmatter каждого артефакта; иначе version drift растёт к 100% и система не прунится.
4. **Знание-контур по запросу, индикаторы автоматически.** decision-log / knowledge-promoter / project-state — только по явному запросу; тренд показывает строка telemetry. Автономное «сохранение всего» засоряет базу и тратит контекст.
5. **Reuse → Compose → Improve → Only then Create.** Не создавать новое (skill/знание/документ), пока существующее не переиспользовано.
6. **Фоновые системы должны использоваться.** scheduler/launchd: задача без расписания (или сломанный сервис) = мёртвый контур.

**Use when:** проектирование или аудит системы знаний для LLM-агента; расширение skill-набора; диагностика «почему система неэффективна»; решение, добавлять ли новый контур.
**Do not use when:** решение конкретной domain-задачи; аудит студии/компании (там `cg-core-consulting`).

[[|**Related knowledge / sources:** system-audit 28.08.2026; [[and_os/lib/skills/system-audit/references/metrics|metrics.md]][[|; [[and_os/lib/skills/telemetry|telemetry.md]]; `.opencode/rules.md` Правила №9–15; `and_os/lib/skills/README.md`.

**Status:** active

---
[[|[[CONTEXT|← Наверх]]