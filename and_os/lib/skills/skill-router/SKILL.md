---
name: skill-router
description: "Use when arbitrating between competing domain skills and routing complex multi-step user prompts to the single primary skill."
version: "1.0.0"
lifecycle: ACTIVE
domain: system
island: 8
context_tier: QUICK
facade_binding: "sys_cli"
modality: DECLARATIVE_KNOWLEDGE
allowed-tools: ["Read", "Grep"]
probe_cmd: "test -f and_os/lib/skills/ROUTING.md"
---
## Scope
Route inbound tasks to exactly one primary skill and minimal necessary secondary skills (Rule №12). This is the canonical routing layer; it does not replace domain skills, `clipping-finder`, `vault-router`, or `sync-context`. Adheres strictly to **Reuse → Compose → Improve → Only then Create**: never invent new tools when existing components suffice.

## Inputs
User prompt, current domain/project focus, and active context sources. In case of ambiguity, declare operational assumptions or ask one targeted clarifying question.

## Context Budget
Context is a strict token budget, not an unlimited resource. Budgets per mode:

| Mode | Budget Scope |
|---|---|
| QUICK | 5–10 relevant snippets |
| WORK | 10–25 snippets |
| STRATEGIC | 25–50 snippets |
| SYSTEM | strictly on-demand |

**Core Invariant:** Stop retrieval as soon as context is sufficient (Rule №9). Never load context "just in case"; for large payloads pipe through `context-compressor`.

## Pipeline / Execution Flow
1. Determine intent, desired outcome, domain project, and operational mode: QUICK / WORK / STRATEGIC / SYSTEM.
2. Evaluate triggers and anti-triggers across the skill registry; select primary skill matching the narrowest robust workflow.
3. Attach secondary skills only if required for an explicit distinct step: retrieval, compression, state, decision, or validation.
4. Select minimum relevant context; pipe large outputs into `context-compressor`.
5. Define composition: linear execution for simple tasks; for composite multi-step tasks, employ [[and_os/lib/skills/task-graph/SKILL|task-graph]] (Rule №20) to construct a DAG execution flow with gates.
6. After finishing a significant task (WORK/STRATEGIC/SYSTEM, not QUICK): log one telemetry line to `and_os/lib/skills/telemetry.md` (see [[and_os/lib/skills/system-audit/references/metrics|metrics.md]]). `project-state`, `decision-log`, and `knowledge-promoter` are strictly on-demand.

## Output Format
```markdown
## ROUTE
**Mode:** QUICK | WORK | STRATEGIC | SYSTEM
**Primary skill:**
**Secondary skills / order:**
**Context sources:**
**Composition / stop condition:**
**Confidence / why:**
```

## Checklist
- [ ] Minimum sufficient skill set selected, not all keyword matches
- [ ] Primary skill does not conflict with anti-triggers
- [ ] Context budget and transition justified

## Anti-Triggers & Constraints
- Do not trigger a skill solely based on a single isolated keyword without a matching task goal
- Do not substitute a specialized domain skill with a generic system routing layer
- Never create a new skill if an existing workflow covers the task requirements
- **External Skills Gateway Heuristic:** When an inbound task introduces a completely novel domain, technology, or framework not covered by our 59 active skills, actively evaluate the global Agent Skills ecosystem (`skills.sh` / `vercel-labs/skills`) via the External Gateway rather than guessing or writing fragile custom instructions from scratch.

## Vault Mutation Protocol (Rule #19 Invariant)
When creating, updating, or patching markdown notes inside the vault:
- DO NOT perform blind raw file overwrites via generic file tools.
- STRICTLY utilize mcp-vault-guard tools (vault_patch, vault_set_frontmatter, vault_read) or microkernel facade:
  python3 and_os/bin/sys_cli.py vault patch --file <path> --find <target> --replace <replacement>
- Ensure zero syntax corruptions in wikilinks (pipe characters) and YAML frontmatter symmetry.
