# 🏛️ SKILL_MODULE_ABI v2.1 — Canonical Skill Architecture

> Standard ABI contract for all skills running within AnD os.

## 1. Dual Modality
- **`EXECUTABLE_ENGINE`**: Active computational tools. Must contain `scripts/` with Python entrypoints accepting `--json` and `--help`.
- **`DECLARATIVE_KNOWLEDGE`**: Cognitive protocols, decision trees, and frameworks. Must contain `references/` with topic-specific markdown files.

## 2. Frontmatter Contract
```yaml
---
name: <kebab-case-name>
description: "Use when ... (observable situation and intent)"
version: 1.0.0
lifecycle: ACTIVE
domain: system | production | health | finance | knowledge | engineering
island: 1..8
context_tier: QUICK | WORK | STRATEGIC
facade_binding: sys_cli | cg_core | doc_cli | tracker_cli
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob"]
probe_cmd: "<canary shell command>"
---
```

## 3. Clean Architecture Invariant (Rule #35 & #50)
- **Reference Standard**: Strictly governed by `clean-code-guardian` (`and_os/lib/skills/clean-code-guardian/SKILL.md`).
- All internal scripts must reside in `scripts/`.
- Zero silent exceptions (`except Exception: pass` is blocked).
- Maximum cyclomatic nesting depth <= 4 (<= 3 for business logic).
- Stateless execution: write mutations only to `and_os/var/` or via `ClosedLoopDispatcher`.
- Mandatory canary test in `scripts/canary.py` with execution latency < 500ms.
