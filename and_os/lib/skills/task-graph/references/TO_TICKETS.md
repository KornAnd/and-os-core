# TO_TICKETS — publishing a compiled task DAG as tickets (v1.2)

Turns a validated task DAG (see `dag_templates.md` + the node contract in
`SKILL.md`) into executable tickets — local scratch issues or GitHub
issues (via the `github-ops` skill, never ad-hoc API calls).

## 1. Tracer-bullet vertical slices (the shape rule)

Every ticket is a **vertical slice**, not a horizontal layer:

- **Narrow but complete** — one user-visible slice of behavior from
  interface to persistence/test, not "all the DB code" or "all the UI".
- **Demoable alone** — a finished slice must be demonstrable on its own
  (a running command, a rendered artifact, a passing DoD check). If a
  slice cannot be demoed without the next slice, the cut is wrong.
- **Fits one fresh context** — a single agent context (or one sitting)
  completes the slice; "resume tomorrow" is a red flag, not a feature.
- **Pre-factoring first** — the slice ships working behavior first;
  refactoring rides in as a separate, later ticket. No big-bang cleanup
  slices inside a feature track.

A DAG that only becomes runnable after all its nodes exist is a
horizontal-layer plan, not a ticket plan — re-cut it along demoable
behavior before publishing.

## 2. Blocking edges

Every edge in the DAG becomes an explicit ticket relation:

- `Blocked by: NN-<slug>` on the dependent ticket.
- A ticket with no blockers is immediately executable; the publish order
  is the topological order of the DAG (critical path first, per the CPM
  invariant in `SKILL.md`).
- One **blocking edge** per dependency: if B is blocked by A and C, list
  both; if the dependency is transitive (A→B→C), only the direct edge is
  written.

## 3. Wide refactors: expand–contract batches

A refactor touching many call sites is never one ticket. Batch it by
blast radius:

1. **Expand** — add the new path alongside the old (both run, old is
   canonical); a per-subsystem ticket, each independently demoable.
2. **Migrate** — switch call sites batch by batch (one ticket per batch,
   each with its own DoD: tests green + no behavior diff).
3. **Contract** — delete the old path in a final ticket that runs only
   after every migration ticket is closed.

Each batch fits one fresh context; the number of batches is chosen so the
rule holds, not the other way around.

## 4. Quiz gate (before publish)

Before any ticket is written, the author must answer, in one line each:

1. What exactly does the finished slice do that it did not do before?
2. How is it demoed (exact command/artifact)?
3. Which tickets block it, and which does it block?
4. What is explicitly OUT of this slice (next ticket)?

If any answer is vague, the slice is re-cut before publishing.

## 5. Templates

**Local (default):** `.scratch/<slug>/issues/NN-<slug>.md`, numbered in
topological (dependency) order, `NN` zero-padded:

```markdown
---
id: NN
title: <vertical-slice title>
status: OPEN
blocked_by: []          # or [NN-<slug>, ...]
blocks: []
dod: <one empirical, checkable sentence>
context: <files/paths this slice touches>
---
<2-4 sentences: what the slice delivers, demo command, what is out of scope>
```

**GitHub:** identical semantics, created through `github-ops` (issue body
= the same fields; `blocked_by`/`blocks` as the "Blocked by"/"Blocks"
lines). The DAG Mermaid from the node contract goes into the parent
issue/README of the `.scratch/<slug>/` bundle.

## 6. Verification

- [ ] Every ticket is a demoable vertical slice (rules §1 all four).
- [ ] Every DAG edge appears as exactly one blocking relation (§2).
- [ ] Wide refactors split into expand → migrate batches → contract (§3).
- [ ] Quiz gate answered for every ticket before publish (§4).
- [ ] Publish order = topological order, critical path first.
