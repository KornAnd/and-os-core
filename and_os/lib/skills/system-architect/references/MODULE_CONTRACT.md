# Module Contract (Template)

> **Reference for `system-architect` Phase 2 (and the dev-flow handoff):** one substantive contract per meaningful module. Reuse an existing contract rather than adding a file per function.
> Provenance (22.11): clean-room adaptation of module-contract concepts (locateam/aicontol, AGPL-3.0 — idea only, original wording).

## Identity & Responsibility

- Module ID / name / revision
- User outcome + requirement references
- Owned responsibility (one sentence)
- Non-goals and excluded behavior (explicit list)

## Contract

- Inputs / outputs and callers
- Data ownership and state transitions
- Invariants and authorization boundaries
- Dependencies and interfaces
- Errors, timeouts, cancellation, recovery

## Acceptance Examples

| Scenario | Given / action | Expected observable result | Verification method |
|---|---|---|---|

- Include meaningful failure cases, not only happy paths.
- The observable contract stays independent of the implementation details being tested.

## Change Impact

- Related contracts / documentation
- Affected tests and approvals when this contract changes
- Current accepted revision + human approval reference

## Invariants

1. A contract change invalidates **only the affected** downstream approvals (smallest re-review); unaffected approvals remain valid — never regenerate the whole design over a local change.
2. A mock or fixture is labelled as such; a sketch does not prove a runtime contract.
3. A skipped feasibility experiment is an explicit waiver with its missing evidence, not a silent omission; waived work is never described as tested or complete.
