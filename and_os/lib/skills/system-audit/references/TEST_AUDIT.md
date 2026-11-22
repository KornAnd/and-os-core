# Test Audit — Value-Bar and Retirement Cards

> Reference for `system-audit` (v1.2). Source: gstack `test-audit`
> (4-question value-bar per test + retirement cards + regression proof),
> adapted to the AnD os suite. The mechanical pre-filter is
> `gate_integrity_probe.py` (G1–G5); this reference is the JUDGMENT layer
> that the static pass cannot do: whether a passing test is WORTH keeping.

## When to run

With every full `system-audit` cycle, and ad-hoc when: a test is proposed
for deletion, a test is flaky, or the suite runtime grows past its budget.

## The 4-question value bar (per test, or per test cluster)

Answer all four, in writing, in the audit report. A test that cannot pass
all four earns a **retirement card** (below) — it is not deleted silently,
and it is not kept silently.

| # | Question | What "no" means |
| :---: | :--- | :--- |
| 1 | **What real defect does this test catch?** Name the incident, the regression class, or the contract it pins. "General coverage" is not an answer. | The test guards a vibe, not a behavior — retire or rewrite it to assert the real defect. |
| 2 | **What is the cost?** Runtime (ms in the suite), maintenance (how often its fixture breaks for non-behavioral reasons), flakiness history. | Cost without proportional protection — candidate for downgrade (slow-mark, cluster) or retirement. |
| 3 | **When was it last red — or would it have caught the last regression in its domain?** Check the actual regression history (audits/, checkpoints, learn notes). | A test that could not have caught any real regression in its domain is a decorative assertion. |
| 4 | **If we deleted it, what breaks that we would care about?** The regression proof: delete (or skip) the test, run the mutation the test claims to guard, and watch the suite go red. | No observable breakage on a plausible mutation = the assertion is not load-bearing. |

## Regression proof (the method behind question 4)

1. Write the mutation down: the concrete production change the test claims
   to catch (a removed check, a changed constant, a dropped branch).
2. Apply the mutation to a copy (or in a scratch worktree — never in the
   live vault state).
3. Run the suite. **Red** → the test is load-bearing; keep it, revert the
   mutation. **Green** → the test does not catch what it claims; it earns a
   retirement card (or a rewrite that actually catches the mutation).
4. Revert the mutation and run the suite to green before closing the audit
   step. A green suite with the mutation still in it is a falsified audit.

A test that "went red once, long ago" without a known incident behind it
scores a **weak** on question 3 — two weaks in a row (two audit cycles)
escalate it to retirement-card status.

## Retirement card (format — one per retired test)

```markdown
### RETIRED: <test name> — <file::test> — <date>
- **Reason:** <which of the 4 questions failed, with evidence>
- **Regression proof:** <mutation applied, suite verdict red/green, or
  "no defect class known for this test">
- **Coverage transferred to:** <the test(s)/gate(s) that now guard the same
  behavior — name them; "nothing, the behavior is gone" is a valid answer>
- **Approved by:** <user confirmation — retirement is a decision, not an
  optimization>
```

Retirement cards are appended to the audit report (and to
`and_os/var/audits/` for full cycles). A retired test
without a card is a finding of its own (G-class: silent gate removal).

## Anti-patterns (declared)

- **Coverage-as-value:** "% coverage up" is never an argument to keep a
  test; value is defect-caught, not lines-touched.
- **Suite as graveyard:** deleting tests to cut runtime without the 4
  questions trades a measurable cost for an unmeasurable risk — the runtime
  problem then goes to question 2 (cluster/slow-mark), not to silent
  deletion.
- **Flaky = delete:** a flaky load-bearing test gets fixed (pinned seed,
  deterministic fixture) or its flake is documented in the card; a flaky
  non-load-bearing test retires with a card. "Quarantine never passes": a
  quarantined flaky test that can never go green again is a retirement
  candidate, not a permanent resident.
