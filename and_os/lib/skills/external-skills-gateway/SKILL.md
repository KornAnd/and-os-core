---
name: external-skills-gateway
description: "Use when searching, inspecting, filtering, or integrating open-source agent skills from skills.sh, Vercel Labs, and GitHub into AnD os."
version: "1.1.0"
lifecycle: ACTIVE
ttl: VOLATILE
reviewed: 2026-11-22
domain: system
island: 8
context_tier: SYSTEM
facade_binding: "sys_cli"
modality: EXECUTABLE_ENGINE
engine: "and_os/lib/skills/external-skills-gateway/scripts/skills_gateway.py"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash"]
probe_cmd: "python3 and_os/lib/skills/external-skills-gateway/scripts/skills_gateway.py --help"
---

# External Skills Gateway

## Purpose
The **External Skills Gateway** serves as the sovereign ingress bridge connecting AnD os with the global Agent Skills ecosystem (Vercel Labs `skills.sh`, open GitHub repositories, and community-curated instruction sets).

It enables the agent to discover proven external solutions for novel domains, inspect them ephemerally, clean them from AI-slop, and safely adapt them into the vault without installing Node.js dependencies (`node_modules`) or violating the microkernel FHS invariants.

---

## Operating Modes

### Mode 1: Search & Discover (`search`)
Search for existing agent skills in open repositories:
```bash
python3 and_os/lib/skills/external-skills-gateway/scripts/skills_gateway.py search "<technology/tool>"
```

### Mode 2: Ephemeral Inspect (`inspect`)
Fetch and review the raw `SKILL.md` of an external skill to solve a single isolated task without polluting the vault. Every inspect now ends with a **Security Vet** section (D5, 17.11): the security_scan SSoT (S1-S9 + 18 PI rule IDs) runs on the fetched content; 🔴 BLOCK lines are payload/exfil classes (secrets, curl|sh, injection phrases), 🟡 ADVISORY lines are hardening signals:
```bash
python3 and_os/lib/skills/external-skills-gateway/scripts/skills_gateway.py inspect "<owner/repo>"
```

### Mode 2.5: Import Gate (`vet`) — D5, 17.11
Mandatory before ANY `register-skill` step: fetches the `SKILL.md` and runs the full deterministic security scan. Exit 0 = clean or advisory-only; exit 1 = blocking findings or an unfetchable (unverifiable) skill — the gate fails closed.
```bash
python3 and_os/lib/skills/external-skills-gateway/scripts/skills_gateway.py vet "<owner/repo>"
```

### Mode 3: Ingest & Sanitize (Rule №15 Integration)
When an external skill needs to be permanently incorporated into AnD os:
1. **Reuse over Create:** First verify whether an existing skill can incorporate the instructions into its `references/` directory.
2. **Security Gate (D5):** `vet` MUST return exit 0 (see Mode 2.5); blocking findings forbid registration until the upstream source is fixed or the payload lines are removed with a documented justification.
3. **Anti-Slop Scrubbing:** Filter the imported `SKILL.md` against [[and_os/docs/specs/ANTI_SLOP_STANDARD|ANTI_SLOP_STANDARD.md]].
4. **FHS Registration:** If registering as a standalone skill, execute:
   ```bash
   python3 and_os/bin/sys_cli.py register-skill --name "<kebab-name>" --desc "<desc>" --domain "<domain>"
   ```
5. **Safety Verification:** Run `python3 and_os/bin/sys_cli.py skills --probe` to ensure ABI v2.1 compliance.
6. **Exception record (scoped deviations, 22.11):** if the adopted helper carries workflow rules that deviate from the AnD os process (auto-advance, forced TDD, extra approval steps), record the exception as a learn note (`sys_cli.py learn --domain system --topic "..." --tags <helper>,exception`): helper identity + version/hash, conflicting rule, permitted deviation, scope (stage/module), expiry/revocation condition, approval evidence. The exception permits only that deviation; a helper's own output or a model-generated allowlist entry is not user approval.

---

## Verification Checklist
- [ ] Query returns specific, high-signal skill repositories.
- [ ] Ephemeral inspect operates in read-only mode with zero local disk writes.
- [ ] Security vet (D5) ran before register-skill: zero 🔴 BLOCK findings; every 🟡 ADVISORY reviewed.
- [ ] Ingested instructions are scrubbed of marketing fluff, binary contrasts, and faux insights.
- [ ] No `node_modules` or `.lock` files are created in the vault.
- [ ] Probe passes cleanly: `sys_cli.py skills --probe`.

## Vault Mutation Protocol (Rule #19 Invariant)
When creating, updating, or patching markdown notes inside the vault:
- DO NOT perform blind raw file overwrites via generic file tools.
- STRICTLY utilize mcp-vault-guard tools (vault_patch, vault_set_frontmatter, vault_read) or microkernel facade:
  python3 and_os/bin/sys_cli.py vault patch --file <path> --find <target> --replace <replacement>
- Ensure zero syntax corruptions in wikilinks (pipe characters) and YAML frontmatter symmetry.
