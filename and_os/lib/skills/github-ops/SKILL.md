---
name: github-ops
description: "Use when searching GitHub repositories, inspecting issues, analyzing pull requests (including modernizing stale PRs), checking CI/CD workflow runs, reading remote code, tracking or creating releases, or publishing/releasing code to GitHub (including zero-leak open-source exports from the Vault)."
version: "1.3.0"
lifecycle: ACTIVE
ttl: STATIC
reviewed: 2026-11-14
domain: engineering
island: 8
context_tier: WORK
facade_binding: "sys_cli"
modality: DECLARATIVE_KNOWLEDGE
allowed-tools: ["Bash", "Read", "Grep", "Glob"]
probe_cmd: "test -x /opt/homebrew/bin/gh || which gh > /dev/null"
---
> **TL;DR:** Sovereign, token-efficient GitHub integration via the official `gh` CLI, per Rule #16 (Think in Code), Rule #44 (Context Bundling), and Rule #59 (Official Toolchain Gate). Every read is projected with `--json` + `--jq` to <100 tokens of actionable data (≥95% context reduction vs raw JSON dumps).
> **Air-Gap Invariant (Rule #58 & #67):** the local Vault is hermetic and not a git repository — this skill operates strictly on external repositories. Never push or export internal Vault notes to public remotes without explicit approval.

## Operating Principles
1. **Official toolchain first:** native `/opt/homebrew/bin/gh`, no unverified wrapper layers; auth via system Keychain. **Pre-write auth gate:** `gh auth status` (token present, correct account, least-privilege scopes) before ANY write.
2. **Context budget protection (Rule #44):** never run bare `gh issue view` / `gh pr diff` without limits or filters — always `--json <fields> --jq <projection>`, null-safe (`// fallback`). Field recipes validated against the live API (last validation: 2026-11-13).
3. **Approval safeguard:** **Reads (autonomous):** `gh search` · issue/pr/run/release `list` + `view` (+ `checks`). **Writes (require user confirmation + approval artifact** — diffstat by change class, full commit message, release-notes draft**):** issue `create`/`close` · pr `create`/`merge`/`review` · release `create` · `git push`.

## Contour A — Daily Operations (token-efficient)
Projection recipes for auth, repo search, issue triage, PR zero-diff analysis, CI health + failed logs, and releases: `references/gh_recipes.md`. Pattern: `gh <cmd> --json <fields> --jq '<projection>'` (<100-token output).

## Contour B — Zero-Leak Release Protocol (Vault → public)
Full 9-step DAG (blacklist locks → path adaptation → preparation gates → 5-level quality filter → payload assembly → fresh-clone E2E → approval artifact → publish + post-publish verification): `references/zero_leak_release_protocol.md`. Deterministic pre-publish audit: `references/scripts/staged_integrity_audit.py <staged-root> [published-clone]` — exit 0 required (10 extended leak patterns + import integrity + delta-vs-published).

**Hard invariants (condensed):**
- **Red Zone (EXPORT FORBIDDEN):** `Nero/` · `Product/` · `Studio/` · `Tasks/` · `Ta-Bu/` · `Story/` · `Book/` · `Industry/` · `Clippings/` · `and_os/var/` + backup artifacts in WORK.
- **Version alignment (Rule #55):** `pyproject.toml` == `system.json` == `RELEASE_LEDGER.json` == `CHANGELOG.md` — one SemVer, no drift.
- **Staging purity:** staging is disposable — never rsync/commit from a staging that has been test-run (re-export first).
- **Fresh-clone E2E before push:** `quick_verify.py` 🟢 + `sys_cli skills --probe` + `pytest` + committed-tree artifact scan = 0 — staging-only green is insufficient.
- **Immutable-history rule:** distinguish *new leak* (must fix) from *already-public class* (explicit decision, record it).
- **Tag discipline:** force-move a release tag only before its first consumption AND disclose; otherwise cut a new tag, keep the old immutable.

## Definition of Done
- [ ] **Contour A:** all output filtered through `--jq` (no terminal dumps >50 lines).
- [ ] **Contour B** (full gate list: `references/zero_leak_release_protocol.md`): zero Red-Zone files in git · paths/identifiers neutralized (no `~`) · storefront manifests present (`.gitignore` covering runtime state, `pyproject.toml`, README, LICENSE, CONTRIBUTING, SECURITY, root CHANGELOG) · version aligned · integrity audit exit 0 · committed tree artifact-free (deterministic scan) · authorship `System Architect <noreply@github.com>` · fresh-clone gates green · tree crystal clean · approval artifact presented + explicit GO · tag discipline · post-publish verification green.

## Vault Mutation Protocol (Rule #19 Invariant)
When creating, updating, or patching markdown notes inside the vault:
- DO NOT perform blind raw file overwrites via generic file tools.
- STRICTLY utilize mcp-vault-guard tools (vault_patch, vault_set_frontmatter, vault_read) or microkernel facade:
  python3 and_os/bin/sys_cli.py vault patch --file <path> --find <target> --replace <replacement>
- Ensure zero syntax corruptions in wikilinks (pipe characters) and YAML frontmatter symmetry.
