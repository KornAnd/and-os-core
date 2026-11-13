---
name: github-ops
description: "Use when searching GitHub repositories, inspecting issues, analyzing pull requests, checking CI/CD workflow runs, reading remote code, or tracking releases."
version: "1.0.0"
lifecycle: ACTIVE
ttl: STATIC
reviewed: 2026-11-11
domain: engineering
island: 8
context_tier: WORK
facade_binding: "sys_cli"
modality: DECLARATIVE_KNOWLEDGE
allowed-tools: ["Bash", "Read", "Grep", "Glob"]
probe_cmd: "test -x /opt/homebrew/bin/gh || which gh > /dev/null"
---

# 🐙 GitHub Operations Skill (`github-ops`)

> 💡 **TL;DR:** Sovereign, token-efficient GitHub integration using the official GitHub CLI (`gh`). Adheres strictly to **Rule #16 (Think in Code / Terminal Filtering)**, **Rule #44 (Context Bundling & Stream Trimming)**, and **Rule #59 (Official Toolchain Gate)**. Replaces heavy raw JSON dumps with precise `--json` and `--jq` filtering to reduce LLM context consumption by $\ge 95\%$.
> 🛡️ **Air-Gap Invariant (Rule #58 & Rule #67):** The local Obsidian Vault is hermetic and not a git repository. This skill operates strictly on external repositories (e.g. in `/WORK/`, Pulsar, Xcode, or open-source GitHub remotes). Never push or export internal Vault notes to public remotes without explicit approval.
> 🔗 **Cross-Links:** [[SYSTEM|SYSTEM.md]] | [[and_os/lib/skills/ROUTING|ROUTING.md]] | [[and_os/lib/skills/REGISTRY|REGISTRY.md]]

---

## 🎯 Architecture & Operating Principles

1. **Official Toolchain First:**
   - Uses `/opt/homebrew/bin/gh` natively without unverified Python wrapper layers.
   - Authentication is managed via system Keychain (`gh auth status`).
2. **Context Budget Protection (Rule #44):**
   - NEVER run bare commands like `gh issue view` or `gh pr diff` without limits or filters.
   - Always project fields using `--json` and format cleanly via `--jq` to return $< 100$ tokens of actionable data.
3. **Approval Safeguard for State Mutations:**
   - **Read Operations (Autonomous):** `gh search`, `gh issue list/view`, `gh pr list/view/checks`, `gh run view`, `gh release list/view`.
   - **Write Operations (Requires User Confirmation):** `gh issue create/close`, `gh pr create/merge/review`, `gh release create`. Always display the payload to the user before submitting.

---

## ⚙️ Execution Contours

Detailed projection patterns, jq recipes, and release invariants are codified in:
- [[and_os/lib/skills/github-ops/references/gh_recipes|gh_recipes.md]] (Contour A: Daily Operations Recipes)
- [[and_os/lib/skills/github-ops/references/zero_leak_release_protocol|zero_leak_release_protocol.md]] (Contour B: Zero-Leak Release Protocol & Air-Gap Locks)

---

### 🌐 CONTOUR A: Operational Interaction (Daily Operations & Telemetry)
*Applied for fast, token-efficient analysis of open repositories, PRs, issues, and CI/CD.*

- **Mode 1: Fast Repository & Code Discovery:**
  ```bash
  /opt/homebrew/bin/gh search repos "<query>" --limit 5 --json fullName,description,stargazersCount,updatedAt --jq '.[] | "\(.fullName) (\(.stargazersCount)★): \(.description)"'
  ```
- **Mode 2: Issue Triage & Summarization:**
  ```bash
  /opt/homebrew/bin/gh issue list --repo <owner/repo> --state open --limit 10 --json number,title,labels,updatedAt --jq '.[] | "#\(.number) [\(.labels | map(.name) | join(","))]: \(.title)"'
  ```
- **Mode 3: Pull Request Analysis (Zero-Diff Invariant):**
  ```bash
  /opt/homebrew/bin/gh pr view <number> --repo <owner/repo> --json title,state,author,files,reviewDecision --jq '{title: .title, state: .state, author: .author.login, review: .reviewDecision, files: [.files[].path]}'
  ```
- **Mode 4: CI/CD Workflow Health & Failed Logs:**
  ```bash
  /opt/homebrew/bin/gh run list --repo <owner/repo> --limit 5 --json databaseId,status,conclusion,name,headBranch --jq '.[] | "[\(.conclusion // .status)] #\(.databaseId) \(.name) (\(.headBranch))"'
  /opt/homebrew/bin/gh run view <run-id> --repo <owner/repo> --log-failed
  ```

---

### 🛡️ CONTOUR B: Core Safe-Publication Protocol (Zero-Leak Release Pipeline)
*Applies strictly when exporting and publishing modules from the Vault to open access on GitHub.*

1. **Total locks on private catalogs (Vault Red Zone):**
   - 🔒 `Nero/` (health, medical records, family, telemetry_sync biometrics, personal goals) — **EXPORT FORBIDDEN**.
   - 🔒 `Product/`, `Studio/`, `Tasks/` (studio full-length animation projects, NDAs, cost estimates) — **FORBIDDEN**.
   - 🔒 `Ta-Bu/`, `Story/`, `Book/` (screenplays, books, startup pitches) — **FORBIDDEN**.
   - 🔒 `Industry/`, `Clippings/` (book summaries, private consulting) — **FORBIDDEN**.
   - 🔒 `and_os/var/`, `and_os/backups/` (real SQLite databases, session tokens) — **FORBIDDEN**.
2. **Path and link adaptation (Autonomous Portability):**
   - Replace absolute paths `~/...` with relative `./`.
   - Replace personal/studio names with system aliases (`System Architect`, `Studio`).
   - Verify the absence of dangling links (Zero-Dangling Links) via `link_guard.py`.
3. **Multi-level quality filter in the staged catalog:**
   - Step 1: `and_os/.venv/bin/python3 and_os/bin/export_kernel.py` (0 leaks).
   - Step 2: `quick_verify.py` inside the staged catalog (`🟢 ALL PHASES PASSED`, 0 critical defects).
   - Step 3: `sys_cli skills --probe` (100% canaries healthy).
   - Step 4: Storefront presence (`README.md`, `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`).
4. **Final publication gate:**
   - Publication is allowed **strictly after Andrey's explicit confirmation** via the command:
     ```bash
     /opt/homebrew/bin/gh repo create <owner>/<repo> --public --source=<path> --push --description "<desc>"
     ```

---

## 📋 Definition of Done Checklist

Before completing any operation through the `github-ops` skill:
- [ ] **Contour A (Everyday):** Output filtered through `--jq` (no terminal dumps $> 50$ lines).
- [ ] **Contour B (Release):**
  - [ ] No file from the Red Zone (`Nero/`, `Product/`, `Ta-Bu/`, `Story/`, `Clippings/`) ended up in git.
  - [ ] Paths adapted; absolute `~` paths fully neutralized.
  - [ ] Package manifests present: `.gitignore`, `pyproject.toml`, `README.md`, `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`.
  - [ ] Bytecode (`__pycache__`, `*.pyc`), test logs (`events.jsonl`), and DB artifacts cleaned.
  - [ ] Commit authorship neutralized: `System Architect <noreply@github.com>` (no local hosts).
  - [ ] `quick_verify.py` returned `🟢 ALL PHASES PASSED`.
  - [ ] Skill canaries `sys_cli skills --probe` confirmed 100% health.
  - [ ] Working tree `git status --porcelain` is crystal clean (0 untracked/dirty files).
  - [ ] Any repository creation or `push` is explicitly confirmed by the user.
