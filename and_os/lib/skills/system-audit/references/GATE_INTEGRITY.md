# Gate Integrity Probe — Criteria & Remediation Protocol

> **Mandatory Reference for `system-audit` (v1.1).**  
> Deterministic detection of **weakened quality gates** — checks that silently stop failing. Adapted from the gstack `/review` Gate Integrity pattern: every weakened gate must reach a named human, not a green log line.

---

## 1. The Five Weak-Gate Classes

| # | Class | Deterministic test | Why it weakens a gate |
| :---: | :--- | :--- | :--- |
| **G1** | Unjustified skip | `@pytest.mark.skip` / `@pytest.mark.xfail` / `@pytest.mark.skipif(cond)` / `pytest.skip()` **without** `reason=` (skipif: needs a condition + reason) | A skipped check still shows "passed"; nobody knows *what* is disabled or *why* |
| **G2** | Unspecific suppression | `# noqa` or `# type: ignore` **without a rule code** (`# noqa: E501` and `# type: ignore[arg-type]` are legal) | A bare suppression silences *any* future error on that line, including regressions |
| **G3** | Assertion-free test | A `test_*` function containing no `assert`, no `raise`, no `pytest.raises`/`warns`, no `self.assert*` (unittest) | The test always passes; it measures the test runner, not the code |
| **G4** | Inflated timing (tests only) | `time.sleep(N > 5)` or `timeout=N > 300` in test files | Gates stretched past their budget hide hangs and make the suite unrunnable; the budgets are 5 s / 300 s |
| **G5** | Swallowed test failure | `try: ... except Exception: pass` (or bare `except`) **inside** a test function | The gate physically cannot fail — the worst class |

Probe: `and_os/.venv/bin/python3 and_os/lib/skills/system-audit/scripts/gate_integrity_probe.py [root ...]`
Scope: `and_os/bin`, `and_os/lib`, `and_os/tests` (`.venv` and `vault_shadow` excluded). Exit 0 clean · 1 findings · 2 usage/syntax error.

**Ownership boundary:** the clean-code guard (`check_code_hygiene.py`) owns code *style* (silent excepts anywhere, nesting, etc.); this probe owns the *integrity of verification gates* (test files, skip/xfail discipline, suppression specificity, timing budgets). No double flagging by design.

## 2. Known Static Limitation (verify before remediation)

Assertions **delegated to module-level helpers** are invisible to the per-function static pass:
```python
def _smoke(args, expect_rc=0):
    res = subprocess.run(...)
    assert res.returncode == expect_rc   # assertion lives in the helper

def test_cli_smoke():                     # G3 will flag this — false positive
    _smoke([BIN, "tool.py", "--help"])
```
Every G3 (and, rarely, G5) finding **must be read** before action: if the test asserts through a helper, close the finding as "helper-delegated, verified" in the audit report; do not "fix" the test. (Real example from the 2026-11-13 vault run: `test_cli_smoke_argparse_shims` asserts through `_smoke()`.)

## 3. Remediation Rules (per class)

| # | Remediation | Prohibited |
| :---: | :--- | :--- |
| G1 | Add `reason="<what> <why> <until-when-or-ticket>"`; re-enable with a dated plan in the report | Deleting the test to make the skip disappear |
| G2 | Replace with a coded suppression (`# noqa: E501`, `# type: ignore[arg-type]`) + a one-line comment why | Keeping a bare suppression "temporarily" |
| G3 | Add the missing assertion(s) for the behavior the test name promises; if the test truly checks nothing — delete it and record the decision | Padding with `assert True` |
| G4 | Restore the original budget; if the budget is genuinely wrong, change the budget **constant in one place** and record the new value in this file | Raising the budget per call site |
| G5 | Restructure so failures propagate (`except ... : raise`, or `pytest.raises` when the failure is the expectation) | Narrowing the except silently |

## 4. Audit Cadence & Recording

- Run the probe at **every full system audit** and after any cycle that touched `and_os/tests`, `and_os/bin`, or CI entry points.
- Findings are recorded in the audit report with: file:line, class, verified-real / helper-delegated, remediation or explicit keep-decision.
- A "keep" decision (weakening is intentional) requires the same evidence bar as any other finding: written reason, owner, review date. Zero silent keeps.
