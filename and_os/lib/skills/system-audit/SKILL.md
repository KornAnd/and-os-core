---
name: system-audit
description: "Use when running full 5-ring Health Grid integrity validations across filesystem syntax, knowledge graph, AST, and background daemons, auditing the integrity of the system's own quality gates (weakened tests, bare suppressions, inflated timing), or auditing local services, the and_os core, or a public package for security vulnerabilities (deterministic secret scan + OWASP Top-10 / STRIDE / AST10 threat modeling)."
version: "2.0.0"
lifecycle: ACTIVE
ttl: STATIC
reviewed: 2026-11-14
domain: system
island: 8
context_tier: WORK
facade_binding: "sys_cli"
modality: EXECUTABLE_ENGINE
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob"]
probe_cmd: "python3 and_os/bin/sys_cli.py audit --help > /dev/null"
---
## Scope
Audit and verify the operational efficiency of the system core itself, rather than domain business workflows. Leverage registry, CONTEXT/KNOWLEDGE, and actual execution footprints; `cg-core-consulting` remains dedicated to studio client consulting.

## Inputs
Audit period, skill registry/index, relevant CONTEXT/KNOWLEDGE maps, decision logs, and task execution telemetry. In the absence of direct measurements, explicitly flag findings as `architectural` rather than statistical.

## Pipeline / Execution Flow
0. Execute automatic Health Grid diagnostics (Think in Code):
   `python3 and_os/bin/sys_cli.py audit --json` (or read cached `and_os/var/system_health.json`).
   Record technical status across Ring 0 to Ring 5 (modules, AST contracts, links, orphans, ports, manifests).
   **Gate Integrity Probe (v1.1):** `and_os/.venv/bin/python3 and_os/lib/skills/system-audit/scripts/gate_integrity_probe.py` —
   deterministic scan for weakened gates (G1 unjustified skips · G2 bare suppressions · G3 assertion-free tests · G4 inflated timing · G5 swallowed test failures). Exit 1 = candidates; **verify each finding manually before remediation** (assertions delegated to helpers are invisible to the static pass — see [[and_os/lib/skills/system-audit/references/GATE_INTEGRITY|GATE_INTEGRITY.md]]).
   **Health Composite (v1.2):** `and_os/.venv/bin/python3 and_os/lib/skills/system-audit/scripts/health_composite.py` —
   weighted 0–10 score over four captured components (suite 0.40 · grid 0.25 · gates 0.20 · diet 0.15) + one JSONL row in `and_os/var/health_history.jsonl`. Trend (up/down/flat) is reported **only at equal coverage** versus the previous row; a capture failure is N/A — the score renormalizes over the captured set and is never padded (`--no-suite` skips the full-suite capture; `--history N` replays rows).
1. Inventory skills: objectives, triggers, anti-triggers, inputs, and outputs.
2. Detect overlaps, gaps, false intersections, and obsolete routes; enforce Reuse → Compose before proposing new skills.
3. Validate context health: freshness, safe links, project states, decisions, knowledge promotion.
4. Evaluate 7-vector metrics from [[and_os/lib/skills/system-audit/references/metrics|metrics.md]]: first-pass success, routing accuracy, context efficiency, knowledge reuse, promotion rate, decision reuse, avg iterations. Sources: `and_os/lib/skills/telemetry.md` + journals.
5. **Test Audit (v1.2):** apply the 4-question value bar — what real defect does it catch · what is the cost · when was it last red (or would it have caught the domain's last regression) · what breaks if deleted (regression proof by mutation) — to gate-probe candidates and every deletion proposal; each deletion earns a **retirement card** and user approval (format in [[and_os/lib/skills/system-audit/references/TEST_AUDIT|TEST_AUDIT.md]]). Silent gate removal is itself a finding.
6. Formulate prioritized remediations with evidence, risk assessment, and owner.

## M2: Security Audit (C11: security-audit absorbed)
Triggers: **before any publication** of Vault code (complements `github-ops` zero-leak — it guards *data* leaving, this guards *vulnerable code* leaving); **after any change** to authentication, file I/O with external input, network gateways, subprocess handling, or persistence in a Pulsar service or core module; **periodic** with the full audit cycle. **Report-only:** the auditor never patches — repair candidates route to `dev-flow`.
Declared out-of-scope (listed in the report as *not assessed*, never assumed safe): browser-side attacks, active network attacks, social engineering, physical access.

### Stage 1 — Deterministic Scan (Think in Code)
```bash
and_os/.venv/bin/python3 and_os/lib/skills/system-audit/scripts/security_scan.py [root ...] [--json]
```
- **Code/config:** S1 secrets (masked: first 4 chars + hash, never full value) · S2 unsafe deserialization · S3 code-injection surface · S4 SQL string interpolation · S6 weak crypto · S7 insecure transport · S8 debug/wildcard-CORS exposure · S9 hardcoded credentials.
- **Agent layer (18 PI-\* rule IDs over .md docs):** injection phrasing, unicode obfuscation (zero-width/bidi/tag), ANSI control bytes (OSC 52, conceal, REP), MCP server registration, sandbox bypass via piped installs, persistent memory writes, unpinned installs, autoload config, missing confirmation gates, six PI-NO-\* missing-guardrail advisories.
- **Triage before action:** `self` / `comment-mention` (scanner artifacts — it flags its own pattern literals), `known-acceptable` (`shell=True` on trusted local input — record the trust boundary), `legit-emoji` (ZWJ), `hardening-backlog` (first-party PI-NO-\*). Exit 0 clean · 1 findings · 2 usage. The `SELF_DETECT_CANARY` line must trip PI-LEAKPHRASE (regression tripwire, `info`).
- **Release gate (v1.3, 18.11 — Rule #70):** `and_os/.venv/bin/python3 and_os/lib/skills/system-audit/scripts/security_baseline_check.py` — re-runs the same scanner over the baseline root (`and_os/`) and intersects the actionable findings with `and_os/etc/security_baseline.json` (frozen 2026-11-18, 199 findings; match key = file+class+context, line-drift tolerant). Any **NEW** actionable finding = release block (exit 1); resolved rows are informational. The baseline is re-frozen **only at release time** via `--update` (it excludes itself from the scan — its recorded rows would be self-referential). Known-benign rows are annotated in the baseline (`benign_annotations`, PI-LEAKPHRASE: 8 canary/comment/test-fixture rows, no real leaks).

### Stage 2 — Threat Model (STRIDE + OWASP Top-10 + AST10)
Application model (assets, entry points, trust boundaries, data flows) ➔ walk STRIDE over each trust boundary ➔ map to OWASP Top-10 with system-specific evidence. Skill-ecosystem targets (external skills, MCP, published packages): additionally walk **OWASP Agentic Skills Top-10 (AST10 v1.0)** and record **shadow features** (capabilities documented but absent in code, and vice versa). Hypotheses without code evidence = `architectural` (Rule #61), never mixed into the measured-findings table. Full method: [[and_os/lib/skills/system-audit/references/THREAT_MODEL_PROTOCOL|THREAT_MODEL_PROTOCOL.md]].

### Stage 3 — Independent Challenge & Explicit Coverage
A fresh subagent (context isolation, `llm-council` protocol) challenges the findings: confirmed / false-positive / missed. The report then states **explicit coverage**: scanned roots/files/classes, modeled boundaries, and what was NOT assessed. Zero silent skips.

**Invariants:** never echo full secrets (masking invariant); never present an unscanned scope as "secure"; local scope only (Vault + 127.0.0.1, no phone-out).

## Output Format
```markdown
# SYSTEM AUDIT — [Date / Period]
**Evidence quality:** observed | partial | architectural
**Findings:**
| Priority | Finding | Evidence | Impact | Action |
**Duplicates / gaps:**
**Routing and context health:**
**Metrics:**
**Decisions required:**
```

## Checklist
- [ ] Conclusions strictly separate observed facts, interpretations, and hypotheses
- [ ] Each recommendation carries evidence and expected operational impact
- [ ] Domain skills are preserved without unneeded modifications
- [ ] Gate Integrity Probe executed; every finding verified (real weakening vs helper-delegated assertion) before remediation
- [ ] Health Composite row appended to the JSONL history; trend stated only at equal coverage; N/A components listed, not hidden
- [ ] Every test deletion/retirement carries a retirement card (4-question verdict + regression proof + approved-by)

## Anti-Triggers & Constraints
- Do not use as a replacement for studio business consulting (`cg-core-consulting`)
- Do not remove or merge skills without confirming actual test coverage
- Do not present architectural assumptions as measured empirical facts

## Vault Mutation Protocol (Rule #19 Invariant)
When creating, updating, or patching markdown notes inside the vault:
- DO NOT perform blind raw file overwrites via generic file tools.
- STRICTLY utilize mcp-vault-guard tools (vault_patch, vault_set_frontmatter, vault_read) or microkernel facade:
  python3 and_os/bin/sys_cli.py vault patch --file <path> --find <target> --replace <replacement>
- Ensure zero syntax corruptions in wikilinks (pipe characters) and YAML frontmatter symmetry.
