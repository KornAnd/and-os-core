# Spec Review Gate (Independent /10 Quality Gate)

> **Mandatory Reference for `system-architect` (Phase 2 exit condition, v1.1).**  
> The specification is scored by an independent reviewer against a fixed 10-point rubric. Scaffolding (Phase 3) is **prohibited below 7/10** (fail-closed).

---

## 1. Position in the Pipeline

- The gate is the **exit condition of Phase 2**: `DESIGN_DOC.md` is not complete until it passes.
- **Fail-closed:** a score below 7/10 blocks scaffolding and handoff; only the failed criteria must be fixed, then re-review.
- Maximum **3 review rounds**; after three failed rounds, escalate to the user with the cumulative failed-criteria list (no silent rework loops).

## 2. Pre-Gate Deduplication (Reuse → Improve)

Before drafting (and again before reviewing):
1. Search the target project root and the Vault for an existing `DESIGN_DOC.md`, `AGENTS.md`, or `docs/schema.json` of the same system.
2. If found: **update the existing spec in place.** A parallel spec for one system is forbidden (Single Source of Truth invariant).
3. If not found: draft the new spec.

## 3. Reviewer Protocol (Context Isolation)

Independence is achieved by **context isolation, not trust**:
1. The reviewer is a **fresh subagent session** that has not seen the design conversation.
2. The reviewer receives exactly three inputs: this file (the rubric), the final `DESIGN_DOC.md`, and the list of existing code paths the spec cites (read-only access).
3. The reviewer does NOT see the design discussion, the user conversation, or the author's intent beyond the spec text.
4. The author **never self-reviews**. A spec scored in the same session that authored it is void.
5. Every criterion point requires an **evidence citation** (spec section or "absent from spec") — no score without evidence.

## 4. Rubric (10 × 1 point)

| # | Criterion | Full point requires |
| :---: | :--- | :--- |
| 1 | Problem & Scope | One-sentence problem statement; explicit in-scope AND out-of-scope lists |
| 2 | Code Discovery Evidence | Existing code/infrastructure read and cited; Reuse → Compose → Improve → Create justification (Rule #69) |
| 3 | Domain / Beacon Mapping | Island + Domain Beacon identified; governing rule numbers listed |
| 4 | Architecture | Clean Architecture layer boundaries explicit; dependencies point inward |
| 5 | Data Contracts | Explicit schema/contract (`docs/schema.json` level); no field names left to guess |
| 6 | Interfaces & Ports | Every endpoint / CLI surface listed; port within `:8080–:8099` and collision-checked (if web) |
| 7 | Error Handling | Error catalog with codes + retryability; fail-fast startup validation |
| 8 | Verification Plan | Measurable Definition of Done (smoke < 200 ms, test commands, expected exit codes) |
| 9 | Runtime Hygiene | 12-factor config, graceful shutdown, `/healthz` + `/readyz`, idempotency where state is written |
| 10 | Zero Secrets / Zero Host Coupling | No hardcoded secrets, no machine paths; project `AGENTS.md` anchor ≤ 300 tokens |

## 5. Verdict Format (fixed)

The reviewer returns exactly:

```
SCORE: <n>/10
| # | Criterion | Points | Evidence (spec section) |
VERDICT: PASS (>= 7/10) | FAIL (< 7/10)
FAILED: <criterion numbers or "none">
```

The verdict block is **appended to the end of `DESIGN_DOC.md`** — the spec carries its own gate receipt.

## 6. Anti-Gaming Invariants

- The rubric is a floor, not a suggestion: the reviewer prompt contains only this file and the inputs — no leniency instructions, no project-specific threshold overrides.
- The 7/10 threshold is a **system invariant**; per-project waiver requires an explicit user decision recorded in the spec.
- A PASS verdict whose evidence column is empty is void — re-review is mandatory.
- Fixing the spec to satisfy the rubric is allowed and expected; editing the rubric to satisfy the spec is not.
