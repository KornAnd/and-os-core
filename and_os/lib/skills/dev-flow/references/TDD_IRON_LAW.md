# TDD Iron Law — Seams, Verify-RED/GREEN, and the 11 Excuses

> Reference for `dev-flow` (v1.1). Sources: obra/superpowers
> `test-driven-development` (Iron Law, Verify-RED/GREEN, rationalization
> table) + mattpocock/skills `tdd` (seams, tautology anti-patterns).
> Adapted to the AnD os suite: full suite = `and_os/bin/run_tests.py`.

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Write code before the test? **Delete it. Start over.** No exceptions:

- Don't keep it as "reference"
- Don't "adapt" it while writing tests
- Don't look at it
- Delete means delete

Implement fresh from tests. Period.

## Seams (pre-confirmation, before the test)

A seam is the boundary where a test can observe behavior: a function or
module with inputs and outputs the test can drive and assert. Before writing
any test, state the seam in one line:

`test observes <function> at <boundary> via <input> -> <observable output>`

- **No seam identified** -> the test will be a tautology (it asserts what the
  code does by construction). Stop and find the boundary: extract a small
  function, add a dependency-injection point. That extraction IS the work.
- **Tautology anti-pattern:** an assertion that restates the implementation
  instead of the requirement. The test must fail if the production change it
  guards is made; assert on real behavior, never on mock behavior.
- **Too-shallow seam:** if the only available seam cannot reproduce the real
  defect (single-caller unit test for a multi-caller bug), a test there gives
  false confidence. **The missing seam is itself the finding** — flag it for
  the next refactor; do not paper over it.

## Verify-RED (mandatory, before implementation)

1. Run the new test: it must FAIL (not error), with the expected message, for
   the reason "feature missing" (not a typo).
2. Test passes immediately? You are testing existing behavior — rewrite it.
3. Test errors? Fix the error and re-run until it fails correctly.

## Verify-GREEN (mandatory, after implementation)

1. The new test passes.
2. **The FULL suite passes:** run
   `and_os/.venv/bin/python and_os/bin/run_tests.py`. A green run of the
   step's test file is NOT a green suite. A task scoping one file bounds the
   deliverable, not the verification.
3. Output pristine (no errors, warnings). Any failure that run shows —
   including one you did not cause — goes into the report by name. A red test
   watched scroll past and not mentioned is a report falsified by omission.

Refactor only after green: remove duplication, improve names, extract
helpers; keep the suite green, add no behavior.

## The 11 Excuses (tautology table)

If the justification in your head matches a row, the work is not TDD. Stop.

| # | Excuse | Reality |
|---|--------|---------|
| 1 | "Too simple to test" | Simple code breaks; the test takes 30 seconds. |
| 2 | "I'll test after" | Tests written after pass immediately — which proves nothing; you never watched it fail. |
| 3 | "Tests-after achieve the same goal (spirit, not ritual)" | Tests-after answer "what does this do?"; tests-first answer "what should this do?". Tests-after are biased by the code already written. |
| 4 | "Already manually tested" | Ad-hoc, unrecorded, unrepeatable. "Worked when I tried it" is not comprehensive. |
| 5 | "Deleting X hours is wasteful" | Sunk cost — that time is spent either way. Keeping code you cannot trust IS the waste. |
| 6 | "Keep as reference, write tests first" | You will adapt it. That is testing after. Delete means delete. |
| 7 | "Need to explore first" | Fine — throw away the exploration, then start with TDD. |
| 8 | "Test hard = design unclear" | Listen to the test: hard to test is hard to use. Fix the seam. |
| 9 | "TDD will slow me down" | TDD is the pragmatic path: catches bugs before commit, enables fearless refactors. "Pragmatic" shortcuts mean debugging in production. |
| 10 | "Manual test faster" | Manual does not prove edge cases; you re-test every change. |
| 11 | "Existing code has no tests" | You are improving it — add tests for the existing code as you go. |

## Red Flags — STOP and start over

Code before test · test after implementation · test passes immediately ·
cannot explain why the test failed · "just this once" · "keep as reference" ·
"already spent X hours" · "this is different because…"

All of these mean: **delete the code, start over with TDD.**

## Exceptions (only with explicit user permission)

Throwaway prototypes (delete them when done) · generated code · pure
configuration files.
