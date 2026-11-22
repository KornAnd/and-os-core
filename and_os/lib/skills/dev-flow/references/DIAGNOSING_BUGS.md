# Diagnosing Bugs — Red-Loop-First Protocol (6 Phases)

> Reference for `dev-flow` (v1.1). Source: mattpocock/skills
> `diagnosing-bugs` (six-phase discipline, "red-capable loop first").
> Adapted: for AnD os the Phase-1 loop is usually a pytest invocation, a
> `sys_cli` subcommand replay, or a curl against a 127.0.0.1 service.

A discipline for hard bugs and performance regressions. Skip a phase only
when explicitly justified in the report.

## Redact (always)

Show commands, outputs and captured artifacts only REDACTED: secrets become
`<REDACTED>`; build loops against env vars so the credential stays in the
environment, never in the shown output (masking invariant).

## Phase 1 — Build the feedback loop (this is the skill)

One named command, already run at least once (show invocation + redacted
output), that is:

- **Red-capable** — drives the actual bug code path and asserts the user's
  exact symptom (red on this bug, green when fixed); not "runs without
  erroring".
- **Deterministic** — same verdict every run. Flaky bugs: raise the
  reproduction rate (loop 100x, stress, narrow timing windows) until
  debuggable.
- **Fast** — seconds, not minutes. Tighten: cache setup, assert the specific
  symptom (not "didn't crash"), pin time/seed/filesystem/network.
- **Agent-runnable** — runs unattended; a human in the loop only as a
  structured last resort.

Ways to build one (roughly in this order): failing test at whatever seam
reaches the bug · curl/HTTP script against a running service · CLI invocation
with a fixture input diffed against a known-good snapshot · replay of a
captured trace/payload · throwaway harness (one service, mocked deps) ·
property/fuzz loop (1000 random inputs) · bisection harness (boot state X,
check, repeat) · differential loop (old vs new version, diff outputs).

**If you catch yourself reading code to build a theory before this command
exists — stop: jumping straight to a hypothesis is the exact failure this
skill prevents. No red-capable command, no Phase 2.**

Genuinely cannot build a loop? Stop and say so: list what was tried, ask the
user for (a) access to the environment that reproduces, (b) a redacted
captured artifact, (c) permission for temporary instrumentation. Do not
hypothesise.

## Phase 2 — Reproduce + minimise

Run the loop; watch it go red. Confirm: the failure is the one the USER
described (wrong bug = wrong fix) · reproducible across runs · exact symptom
captured (message / wrong output / slow timing). Then shrink the repro to the
smallest scenario that still goes red — cut elements one at a time, re-run
after each cut, keep only what is load-bearing. A minimal repro shrinks the
hypothesis space and becomes the clean regression test in Phase 5.

## Phase 3 — Hypothesise

3–5 RANKED, FALSIFIABLE hypotheses BEFORE testing any. Single-hypothesis
generation anchors on the first plausible idea. Each states its prediction:

> "If <X> is the cause, then <changing Y> will make the bug disappear /
> <changing Z> will make it worse."

No prediction = a vibe: discard or sharpen. Show the ranked list to the user
before testing (a cheap re-ranking checkpoint; proceed if the user is AFK).

## Phase 4 — Instrument

Each probe maps to a specific Phase-3 prediction. Change ONE variable at a
time. Prefer debugger/REPL over targeted logs at the boundaries that
distinguish hypotheses; never "log everything and grep". Tag every debug log
with a unique prefix (e.g. `[DEBUG-a4f2]`) — cleanup becomes one grep.
Perf branch: establish a baseline measurement first (timing harness,
profiler, query plan), then bisect. Measure first, fix second.

## Phase 5 — Fix + regression test

Write the regression test BEFORE the fix — but only at a CORRECT seam (the
test must exercise the real bug pattern as it occurs at the call site). If no
correct seam exists, that itself is the finding: the architecture is
preventing the bug from being locked down — flag it. When a seam exists:

1. Turn the minimised repro into a failing test at that seam.
2. Watch it fail. If the red was forced by mutating code or a fixture,
   `diff` against a pristine copy to prove the mutation landed.
3. Apply the fix.
4. Watch it pass.
5. Re-run the Phase-1 loop against the ORIGINAL (un-minimised) scenario.

## Phase 6 — Cleanup (required before "done")

- Original repro no longer reproduces (re-run the Phase-1 loop)
- Regression test passes (or absence of seam is documented)
- All `[DEBUG-…]` instrumentation removed (grep the prefix)
- Throwaway prototypes deleted (or moved to a clearly-marked debug location)
- The correct hypothesis is stated in the commit/PR message, so the next
  debugger learns
