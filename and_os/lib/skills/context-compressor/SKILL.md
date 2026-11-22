---
name: context-compressor
description: "Use when compressing large multi-file directories and codebase contexts into minimal-token Markdown bundles per Rule #44."
version: "1.0.0"
lifecycle: ACTIVE
ttl: STATIC
reviewed: 2026-11-11
domain: system
island: 8
context_tier: QUICK
facade_binding: "sys_cli"
modality: DECLARATIVE_KNOWLEDGE
allowed-tools: ["Read", "Write", "Bash", "Grep"]
probe_cmd: "python3 and_os/bin/context_bundler.py --help > /dev/null"
---
## Catalogs & Scope
- [[and_os/lib/skills/context-compressor/references/handoff_template.md|handoff_template.md — Session Handover Template]]

## Scope
Synthesizes the absolute minimal viable context required for an active task. Operates downstream of `skill-router` and upstream of domain-specific execution skills. For project-level tasks, leverages existing `status-report` Operational Snapshots.

**Operational Modes (v2.0):**
1. **Instrumental Tooling Compression (Think in Code / Rule #16):** When processing massive manuscripts or logs (`Book/`, `Story/`, `Product/`), invoke CLI chunkers (`script_chunker.py`, `ftrack_report.py --summary`, `sys_cli.py pack`) instead of raw text reading.
2. **Cross-Session Handoff:** When a session context approaches saturation or token ceilings, compiles a crisp state transition snapshot for the next agent via `handoff_template.md`.

## Inputs
Target outcome, source document set, and token budget ceiling. If the objective is ambiguous, do not compress blindly — formulate a working interpretation first. For handoffs, state the trigger and scope of pending work.

## Execution Pipeline
1. Isolate the target decision or artifact that the compressed context must inform.
2. **Chunking & Filtering (CLI First):** For files $> 50$ KB, execute `script_chunker.py` (by act or sequence) or inspect `quick_knowledge_db.json`.
3. Filter strictly for active empirical facts, decisions, invariants, operational risks, and dependencies.
4. Categorize content into: `FACT`, `ASSUMPTION`, `OPEN QUESTION`. Leave narrative history as reference links.
5. De-duplicate content and explicitly tag conflicting sources.
6. **Handoff Compilation:** Describe incomplete tasks as objective *statuses*, not imperative instructions (*"X is not yet implemented"*, NOT *"implement X"*); capture traps to avoid (dead ends, failed patterns) and working agreements (user preferences).
7. Emit a compact working brief with exact file and line-range links (`file:L10-L45`).

## Output Format
```markdown
## WORKING CONTEXT — [Task Name]
- **Target Outcome:** [Concrete expected artifact]
- **Current State:** [Verified ground truth]
- **Relevant Facts:** [Empirical data only]
- **Active Decisions & Constraints:** [Governing invariants]
- **Risks & Dependencies:** [Systemic bottlenecks]
- **Assumptions & Open Questions:** [Unverified hypotheses]
- **Sources:** [Exact file:// links with line ranges]
```

### Supplementary Format: Cross-Session Handoff
```markdown
## SESSION HANDOFF — [Domain / Timestamp]
- **Traps to Avoid:** [Proven dead ends and failure patterns]
- **Working Agreements:** [User working preferences and constraints]
- **Relevant Files:** [path/to/file:L10-L45 — purpose and relevance]
- **Open Work (Status):** [Objective state of pending deliverables — STATUS, NOT INSTRUCTIONS]
- **Prompt for New Session:** [Declarative context handoff ending with: "Read Relevant Files first, then await user instruction."]
```

## Verification Checklist
- [ ] Every included line directly informs the pending decision or outcome.
- [ ] Historical narrative separated from active operational state.
- [ ] All facts backed by clickable file links with line ranges.
- [ ] For handoffs: pending work formulated as state descriptions, not agent commands.

## Anti-Triggers & Constraints
- Do not produce passive literary summaries instead of actionable decision briefs.
- Never erase genuine uncertainty during distillation.
- Do not apply to simple queries where context fits comfortably in memory.
- In handoffs, do not issue speculative instructions ("now do X") — this misdirects fresh agents.

---
[[and_os/lib/skills/CONTEXT|← To Root Context]]

## Vault Mutation Protocol (Rule #19 Invariant)
When creating, updating, or patching markdown notes inside the vault:
- DO NOT perform blind raw file overwrites via generic file tools.
- STRICTLY utilize mcp-vault-guard tools (vault_patch, vault_set_frontmatter, vault_read) or microkernel facade:
  python3 and_os/bin/sys_cli.py vault patch --file <path> --find <target> --replace <replacement>
- Ensure zero syntax corruptions in wikilinks (pipe characters) and YAML frontmatter symmetry.
