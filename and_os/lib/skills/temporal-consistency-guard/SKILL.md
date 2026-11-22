---
name: temporal-consistency-guard
description: "Use when verifying visual and narrative continuity, character wardrobe constancy, and lighting consistency across AI video shots."
version: "1.1.0"
lifecycle: ACTIVE
ttl: STATIC
reviewed: 2026-11-15
domain: ai
island: 7
context_tier: WORK
facade_binding: "cg_core"
modality: DECLARATIVE_KNOWLEDGE
allowed-tools: ["Read", "Write", "Grep", "Glob"]
probe_cmd: "test -d and_os/lib/skills/temporal-consistency-guard"
---
# 🛡️ temporal-consistency-guard — Animation Sequence Deflicker & Continuity Gate

> **Purpose:** Canonical Primary Skill for verifying temporal consistency across AI-rendered frame sequences, calculating optical variance, and enforcing deterministic render contracts (hyperframes-contract standard).  
> **Master CLI Engine:** `and_os/bin/temporal_consistency_guard.py` · **Microkernel facade:** `python3 and_os/bin/sys_cli.py consistency <sequence_dir>`
> **Contract Schema:** [[and_os/lib/skills/temporal-consistency-guard/references/render_contract.schema.json|render_contract.schema.json]]

---

## ⚙️ Execution Protocol

```bash
# Standard evaluation of frame sequence directory
python3 and_os/bin/temporal_consistency_guard.py "output/frames/sh_010/"

# Deterministic Render Contract Evaluation (hyperframes-contract mode)
python3 and_os/bin/temporal_consistency_guard.py "output/frames/sh_010/" \
  --contract "and_os/lib/skills/temporal-consistency-guard/references/render_contract.schema.json" \
  --threshold 0.12

# Output structured JSON metrics for pipeline gating
python3 and_os/bin/temporal_consistency_guard.py "output/frames/sh_010/" --json

# Persist QA Report for shot review
python3 and_os/bin/temporal_consistency_guard.py "output/frames/sh_010/" --out "output/frames/sh_010/QA_Report.md"
```

## 📐 Deterministic Continuity Invariants
1. **Zero Silent Jumps:** Luminance jumps exceeding `max_luma_variance` (default 0.08) are instantly flagged.
2. **Anchor Stability:** Spatial drift of key markers exceeding `max_drift_px` triggers rejection back to ComfyUI/Blender.
3. **No Decorative Passes:** Every report must output exact computed flicker scores versus the locked threshold.

## Vault Mutation Protocol (Rule #19 Invariant)
When creating, updating, or patching markdown notes inside the vault:
- DO NOT perform blind raw file overwrites via generic file tools.
- STRICTLY utilize mcp-vault-guard tools (vault_patch, vault_set_frontmatter, vault_read) or microkernel facade:
  python3 and_os/bin/sys_cli.py vault patch --file <path> --find <target> --replace <replacement>
- Ensure zero syntax corruptions in wikilinks (pipe characters) and YAML frontmatter symmetry.
