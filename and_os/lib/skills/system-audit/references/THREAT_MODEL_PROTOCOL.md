# Threat Model & Challenge Protocol

> **Mandatory Reference for `security-audit` (v1.1), Stages 2 and 3.**
> Stage 1 (`security_scan.py`) is deterministic and mechanical. Stages 2-3
> are judgment: they turn findings into a verdict with evidence, and state
> explicitly what was NOT assessed. Zero silent skips.

---

## 1. Stage 2 — Threat Model (STRIDE over the application model)

### 1.1 Build the application model (before any STRIDE pass)

Answer all four, in writing, in the report:

1. **Assets** — what is worth protecting (secrets, user data, service availability, integrity of published code, disk state in `and_os/var`).
2. **Entry points** — network (127.0.0.1 :8080-:8099), filesystem (Vault paths), CLI/stdin, local manifests (SKILL.md frontmatter, project manifests), environment variables.
3. **Trust boundaries** — e.g. agent <-> Vault, Vault <-> Pulsar services, local operator <-> published package. Every crossing is a STRIDE locus.
4. **Data flows** — where secrets move (env -> process memory -> reports). Note every flow that passes through a report, log, or telemetry entry (the masking invariant applies there, not only in the scanner).

### 1.2 STRIDE pass

Walk every trust boundary; for each, ask the six questions and record
either **measured evidence** (code line, repro, config value) or the mark
`architectural` (Rule #61 — hypothesis, never mixed into the measured table):

| # | Threat | Standing question |
| :---: | :--- | :--- |
| S | Spoofing | Can a local caller masquerade as another (fake service identity, forged manifest fields)? |
| T | Tampering | Can Vault state or manifests be modified without audit (direct file write bypassing `sys_cli`)? |
| R | Repudiation | Can an action run without a trace (missing audit event, unlogged deploy)? |
| I | Information disclosure | Can a secret/value reach a report, log, telemetry, or published artifact in full? (Masking invariant check.) |
| D | Denial of service | Can one local input stall a service (unbounded read, no timeout, port exhaustion in :8080-:8099)? |
| E | Elevation of privilege | Can a low-privilege local caller reach a higher-privilege path (probe_cmd injection via an untrusted SKILL.md, shell surface with attacker-controlled input)? |

### 1.3 OWASP Top-10 mapping

Map each STRIDE finding to the OWASP class it instantiates (A01 broken
access control, A02 cryptographic failures, A03 injection, A05 security
misconfiguration, A07 identification/authentication failures, A08 software
and data integrity failures, A09 logging/monitoring failures, A10 SSRF)
with the system-specific evidence. OWASP is a *mapping aid*, not the model:
the model is the trust-boundary walk.

### 1.4 Shadow features (capability audit)

During the application-model pass, cross-check the documented surface
against the implemented surface and record both directions:

- **Documented, not in code** — a capability advertised in a skill
  description, reference, or doc that has no code path behind it. Risk:
  operators and agents trust a guard that does not exist; the gap is a
  report finding (severity by blast radius).
- **In code, not documented** — a capability (port, file write, network
  call, subprocess) that no doc mentions. Risk: *the undocumented path is
  the path nobody audits* — it sits outside every review, outside the
  threat model, outside the scanner's declared scope. Each one is a
  Stage-2 finding (Tampering / Information disclosure, per the path) until
  documented and scoped, or removed.

Method (deterministic): collect the documented verbs (the SKILL.md
description + references) and the implemented verbs (subprocess, network
calls, filesystem writes, ports bound), then diff the two sets. Every
unmatched entry goes to the report with its evidence line.

### 1.5 AST10 checklist (OWASP Agentic Skills Top-10, v1.0 — 2026)

For skill-ecosystem targets (external skills under review, MCP surfaces,
published packages, registry-sourced content) walk the ten skill-layer
risks in addition to the STRIDE pass. Record measured evidence or the
`architectural` mark per row:

| # | Risk | Standing question (local scope) |
| :---: | :--- | :--- |
| AST01 | Malicious Skills | Is the artifact's provenance verifiable (author, hash, registry scan) before activation? |
| AST02 | Supply Chain Compromise | Are dependencies pinned (toolchain.lock, `==` pins) and the install path audited (PI-SUPPLY-CHAIN)? |
| AST03 | Over-Privileged Skills | Does `allowed-tools` / the binding grant the minimum surface the task needs (least privilege)? |
| AST04 | Insecure Metadata | Is the SKILL.md frontmatter schema-validated (`validate_skill.py`) and parsed safely (no eval of metadata)? |
| AST05 | Untrusted External Instructions | Is every fetched/ingested document (web, registry, issues) treated as passive data — Untrusted Content Guard — and delimit-scanned (PI-NO-DELIMIT)? |
| AST06 | Weak Isolation | Do skill scripts run with the local-scope boundary (no egress, 127.0.0.1 only) stated in the report? |
| AST07 | Update Drift | Is the skill version/reviewed date pinned (REGISTRY + diet baseline + checkpoints) so drift is detectable? |
| AST08 | Poor Scanning | Is the artifact covered by a deterministic scan (Stage 1, incl. the 18 PI rule IDs) AND a judgment pass (Stage 3)? Pattern-only scanning misses natural-language injection — the challenge stage is the semantic layer. |
| AST09 | No Governance | Is the skill in the REGISTRY with an owner, telemetry, and audit trail (telemetry.md, audits/)? |
| AST10 | Cross-Platform Reuse | When a skill moves between platforms/formats, does its security metadata (allowed-tools, risk notes) survive the translation, or is it re-validated at the target? |

Empirical context (why the checklist exists, 2026): Snyk ToxicSkills —
36.82% of 3,984 scanned skills with flaws, 76+ confirmed malicious
payloads; ClawHavoc — 1,184 malicious skills in one registry campaign.
The skill layer is an actively attacked surface, not a theoretical one.

## 2. Stage 3 — Independent Challenge

A **fresh subagent** (context isolation; the author never challenges its own
findings — `llm-council` cross-harness protocol) receives: the Stage-1 table,
the Stage-2 table, and the application model. It returns per finding:

- **confirmed** — the risk is real as described;
- **false-positive** — with the reason (helper-delegated logic, constant
  mistaken for interpolation, self-detection, comment mention);
- **new** — a risk the first pass missed (the challenge exists to produce at
  least the *attempt*; "found nothing new" is a valid result, stated as such).

The challenged table (original + verdict + note) is Stage 3 of the report.

## 3. Severity Rubric (applied to the challenged table)

| Severity | Definition (local scope) | Example |
| :--- | :--- | :--- |
| **critical** | Full secret reachable from a published artifact or untrusted local input; RCE surface with external input | live token in a published package |
| **high** | Credential exposure inside the Vault reachable by any local process; injection with attacker-influenced local input | unmasked secret in a report template |
| **medium** | Misconfiguration with local-only blast radius (debug endpoint, wildcard CORS on a local port, no auth on a 127.0.0.1 admin surface) | `debug=True` in a shipped app config |
| **low** | Advisory: weak-but-intentional pattern with documented purpose (`# nosec` boundary stated) | `shell=True` in the terminal engine |
| **info** | Self-detection, comment mention, or observation without exploitable path | the scanner flagging its own regex literal |

## 4. Explicit Coverage (report section 4 — never omitted)

- **Scanned:** roots, file count, class list, scanner version.
- **Modeled:** every trust boundary from 1.1 with its STRIDE status.
- **NOT assessed (declared):** browser-side attacks (no bundled browser),
  active network attacks, social engineering, physical access, and any
  service that was not running during the audit. Not assessed = not assumed
  safe; the report says so in words.

## 5. Known Limitations of Stage 1 (what the deterministic pass cannot see)

1. **Self-detection:** the scanner's own pattern literals and docstrings
   match its own patterns. Always triaged as `self`.
2. **Comment mentions:** comments that describe a guarded pattern
   (e.g. "blocks eval(...) calls") match. Triaged as `comment-mention`.
3. **Static, line-oriented:** multi-line string concatenation, values built
   across lines, and import-time side effects are invisible.
4. **Receiver-blind heuristics:** `execute(...)` on a non-database object
   (the terminal engine) is still flagged; the receiver must be read at
   triage.
5. **No data flow:** whether a flagged value actually reaches an output is
   Stage-2 work (Information disclosure), not Stage-1.

## 6. Report Discipline

- Report-only invariant: the audit modifies no file; repair candidates are
  proposed with an owner (`dev-flow` or user) and re-verified by a re-audit.
- Every secret shown anywhere in the report is masked (first 4 chars +
  `[sha256:8]`). A full value in a report is itself a Stage-2 finding
  (Information disclosure, severity high).
- Hypotheses stay out of the measured table: `measured` vs `architectural`
  is a per-row column, never a vibe.
