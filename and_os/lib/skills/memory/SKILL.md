---
name: memory
description: "Use when orchestrating closed-loop memory in AnD os: running Pre-flight Recall to retrieve negative constraints, Post-flight Learning to crystallize solutions via sys_cli learn, managing accumulated memory (review, prune, export digests), or recording irreversible architectural, business, and personal decisions (ADRs)."
version: "2.0.0"
lifecycle: ACTIVE
ttl: VOLATILE
reviewed: 2026-11-15
domain: knowledge
island: 1
context_tier: WORK
facade_binding: "sys_cli"
modality: EXECUTABLE_ENGINE
engine: "and_os/bin/sys_cli.py"
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob"]
probe_cmd: "test -d and_os/lib/skills/memory"
---
## Catalogs & Scope
- [[Nero/CONTEXT|Nero — Knowledge map (knowledge/engineers learn notes)]]
- [[Clippings/quick_knowledge_db|quick_knowledge_db — In-memory BM25 index (<15ms)]]
- [[Nero/profile/my/decision_log|decision_log.md — ADR registry]]
- [[and_os/lib/skills/ROUTING|ROUTING — Skills routing and domain arbitration]]

**Scope:** universal memory engine enforcing **Rule #13 (Retrieval → Context → Execution → Memory)** and **Rule #7 (Closed-Loop Life Cycle)**: four deterministic modes (C11: decision-log absorbed as M4).

## ⚙️ Execution Commands

### Mode 1: Pre-flight Recall (Read Memory)
Before assembling assets, code, or story outlines, query accumulated domain experience:
```bash
python3 and_os/bin/sys_cli.py find "<keyword>" --limit 3
# Examples: find "parallax" (ComfyUI depth/lineart) · find "логлайн" (logline formulas) · find "playblast"
```

### Mode 2: Record Verified Solution (Write Memory)
Triggered when a roadblock is resolved or the user gives explicit guidance ("remember this", "don't do X", "correct way is Y"):
```bash
python3 and_os/bin/sys_cli.py learn \
  --domain "<blender|comfyui|davinci|swift|xcode|core|user|story|article|process|finance>" \
  --topic "<Concise Pattern Title>" \
  --problem "<Observed failure mode, symptom, or user objection>" \
  --solution "<Deterministic verified fix or invariant>" \
  --tags "comma,separated,tags"
```

### Mode 3: Manage Memory (Review / Prune / Export, v2.1)
Quarterly or after large skill cycles; mandatory when a domain holds >30 active records:
```bash
python3 and_os/bin/sys_cli.py find "<domain-keyword>" --json --limit 50
```
**Prune** superseded/stale/duplicate records: status transition `VERIFIED` ➔ `PRUNED` + `pruned:` date + `prune_reason` (+ `superseded_by`) via `sys_cli.py vault patch`. **Zero physical deletion** — memory is accumulated evidence. **Export:** per-domain digest of ACTIVE records ➔ `Nero/knowledge/memory_export_<domain>_<YYYY-MM-DD>.md`. Full criteria: [[and_os/lib/skills/memory/references/MANAGE_PROTOCOL|MANAGE_PROTOCOL.md]].

### Mode 4: ADR Decision Records (C11: decision-log absorbed)
Formal Architecture Decision Records for irreversible architectural/business/technology/personal choices. Invoked **ONLY upon explicit user command** ("record decision"); routine tracking is the `D(+/-)` telemetry column.
1. Verify no existing record addresses the same architectural question; mark displaced decisions `SUPERSEDED` (never erase history).
2. Document rationale, evaluated alternatives, blast radius, owner, review trigger; unratified choices are `HYPOTHESIS` pending confirmation.
3. Bridge to `status-report` snapshots and source files; persist via `file-lifecycle` (route ➔ register in CONTEXT.md), then trigger sync.

**Lifecycle:** `ACTIVE` ➔ `SUPERSEDED` ➔ `REJECTED` ➔ `ARCHIVED`. Never delete — adjust statuses only.
```markdown
## D-[ID] — [Decision Title]
- **Date / Owner:** YYYY-MM-DD / [Owner] · **Status:** ACTIVE|PENDING|SUPERSEDED|REJECTED|ARCHIVED
- **Context & Drivers** · **Alternatives Considered** · **Consequences & Trade-Offs**
- **Review Trigger** · **Supersedes / Related:** [[D-xxx]] · **Sources:** file:// links
```
Anti: no ADR for trivial fixes without long-term blast radius; never present an agent recommendation as an adopted decision.

---

## 🛑 Proof of Reality Gate (Validation Invariant)
Before promoting any pattern into long-term memory:
1. Must be verified through **executed code, terminal output, physical asset inspection, or explicit user confirmation**.
2. Speculative LLM hypotheses and unverified suggestions are **strictly forbidden** from promotion.
3. Every learned record receives `status: VERIFIED` and temporal timestamps.

## 📋 Verification Checklist
- [ ] Pre-flight memory query executed before starting complex tasks
- [ ] Pattern registered via `sys_cli.py learn` with exact domain; note in `Nero/knowledge/engineers/`; index verified via `sys_cli.py find`
- [ ] Manage pass (when due): no stale records left `VERIFIED`; pruned carry `prune_reason`; digest exported
- [ ] (M4) ADR: alternatives + trade-offs captured; legacy decisions marked `SUPERSEDED`, never deleted
- [ ] Telemetry logged automatically (`sys.learn`)

[[and_os/lib/skills/CONTEXT|← To Root Context]]
