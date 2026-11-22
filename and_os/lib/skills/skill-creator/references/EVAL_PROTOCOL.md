# EVAL_PROTOCOL — routing evaluation for skill descriptions (v1.2)

Mechanics: `scripts/eval_skill.py` (pure stdlib, TDD-covered). The protocol
defines how descriptions are measured, compared, and admitted to change.

**Principle: diet by evidence, not taste.** A description may be rewritten
only when the A/B gate passes on a real routing measurement.

## 1. What is measured

A skill description's *trigger behavior*: given a user prompt and the full
description set, does a fresh routing agent pick this skill? The measured
unit is a **decisions log** produced by an LLM that never sees the expected
answers. The harness (`eval_skill.py`) is deterministic scoring; the LLM is
the instrument. Neither is replaced by assumptions (Zero-Hype).

## 2. Benchmark schema (`<skill>/benchmark.json`)

```json
{
  "skill": "kebab-name",
  "version": "1.0.0",
  "created": "YYYY-MM-DD",
  "prompts": [
    {"id": "uniq-slug", "prompt": "realistic user prompt",
     "expected": "kebab-name", "decoys": ["rival-skill"]}
  ]
}
```

Design rules:
- 6–10 prompts; more is overfitting surface, not signal.
- Every prompt must be a prompt a real user would send; `expected` always
  equals the benchmark's own skill (B004) — per-skill benchmarks measure
  trigger recall, pooled runs measure cross-skill precision.
- `decoys` are the rivals a router actually confuses (from the routing
  atlas / observed misses), not strawmen.
- Prompts are versioned with the skill; changing a benchmark is a design
  change — record it in the skill's review note.

## 3. Decisions log (the measurement)

Contract for the routing subagent (fresh context, no task history):
1. Input: the full set of skill `name` + `description` pairs (all
   registered skills) and the benchmark prompt list. Nothing else — no
   expected answers, no decoy hints, no SKILL.md bodies.
2. Output: strict JSON, one decision per prompt id:
   `{"decisions": [{"id": "…", "chosen": "skill-name"}]}`.
3. The subagent chooses the single primary skill per prompt (Rule №12
   semantics); ties are broken by its own judgment, not by asking.

The log records provenance: `benchmark` (path/sha), `model` (which
harness/model routed), `date`.

## 4. The 60/40 cycle

`eval_skill.py split --benchmark b.json --out-dir d/` produces
`<stem>.optimize.json` (60%) and `<stem>.holdout.json` (40%), deterministic
for a fixed seed. Iterate on candidate descriptions against the **optimize**
split only; the **holdout** split is consumed exactly once, at the end, to
confirm the candidate did not memorize the training prompts.

## 5. The A/B gate

```
eval_skill.py ab --benchmark b.json \
  --decisions-a decisions_baseline.json \
  --decisions-b decisions_candidate.json
```

- A = decisions under the current description, B = under the candidate.
  Both logs must be produced by the same routing procedure (§3).
- `delta = accuracy_A - accuracy_B`; **PASS only when delta <= 0**.
- PASS → the candidate is admitted and the benchmark's baseline log is
  replaced; FAIL → the candidate is rejected, the current description
  stands. A tie (delta = 0) admits the candidate only if it also shortens
  the description (the diet direction).

## 6. Reading the score

- `recall` (per skill) — how often the skill is picked when it should be.
- `precision` — pooled runs only: picks of the skill that were wrong.
- `decoy_captures` — which rival actually swallows the prompt; this names
  the description pair to sharpen, not "make everything louder".
- Misses with `chosen` outside the decoy set = a third skill entered the
  confusion; add it as a decoy and re-measure before touching text.

## 7. Rollout

Benchmarks are mandatory for: new skills (pilot before the first
description is considered stable), and any skill whose description was
rewritten in the last cycle. Current pilot: `deep-research`
(`and_os/lib/skills/deep-research/benchmark.json`). Remaining skills are
benchmarked on demand when a routing miss is observed in the log.

---
[[Vault|← Vault]]
