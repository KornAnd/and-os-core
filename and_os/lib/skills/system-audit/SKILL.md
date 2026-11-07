---
name: system-audit
description: "Use when running full 5-ring Health Grid integrity validations across filesystem syntax, knowledge graph, AST, and background daemons."
version: "1.0.0"
lifecycle: ACTIVE
domain: system
island: 8
context_tier: WORK
facade_binding: "sys_cli"
modality: DECLARATIVE_KNOWLEDGE
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
1. Inventory skills: objectives, triggers, anti-triggers, inputs, and outputs.
2. Detect overlaps, gaps, false intersections, and obsolete routes; enforce Reuse → Compose before proposing new skills.
3. Validate context health: freshness, safe links, project states, decisions, knowledge promotion.
4. Evaluate 7-vector metrics from [[and_os/lib/skills/system-audit/references/metrics|metrics.md]]: first-pass success, routing accuracy, context efficiency, knowledge reuse, promotion rate, decision reuse, avg iterations. Sources: `and_os/lib/skills/telemetry.md` + journals.
5. Formulate prioritized remediations with evidence, risk assessment, and owner.

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
