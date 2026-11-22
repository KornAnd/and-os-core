# Zero-Leak Open-Source Release Protocol (Air-Gap Release Standard)

> **Mandatory Reference for `github-ops` Skill (Contour B: Zero-Leak Release Pipeline).**  
> Enforces mathematical data isolation (Rule #57 & Rule #58) and sovereign air-gap integrity when exporting components from AnD os to public GitHub repositories.  
> v1.1 (2026-11-13): deterministic pre-publish gates added after the v1.0.0 publication cycle (fresh-clone E2E, staging purity, payload purity, tag discipline).

---

## 🔒 1. Absolute Blacklist Locks (Vault Air-Gap Red Zone)

The following directories in the Obsidian Vault are **strictly locked** and mathematically excluded from any export or git tracking:

| Directory | Contained Data | Leak Risk | Invariant Enforcement |
| :--- | :--- | :---: | :--- |
| **`Nero/`** | Medical health records (UC/chronic_condition), clinic reports, telemetry_sync biometrics, family, financial ledger, 25 personal life goals. | **CRITICAL** (HIPAA / Privacy) | Hardcoded blacklist in `export_kernel.py`. Automated regex leak pattern scan. |
| **`Product/`, `Studio/`, `Tasks/`** | Studio production NDA (full-length animated features "Kot", "Mars"), artist rates, project sprint tasks. | **CRITICAL** (Commercial NDA) | Never copied to staging. Name sanitization rule replaces studio & project names. |
| **`Ta-Bu/`, `Story/`, `Book/`** | Screenplays, story bibles, book chapters, startup pitch decks & valuation metrics. | **HIGH** (Intellectual Property) | Strictly excluded from whitelist. |
| **`Industry/`, `Clippings/`** | Book summaries, raw research clippings, private enterprise consulting memos. | **MEDIUM** (Client Confidentiality) | Excluded from export whitelist. |
| **`and_os/var/`** (Vault runtime state) + backup artifacts in WORK (via `sys_cli backup`) | Live SQLite databases, session tokens, APFS snapshot logs, personal state records. | **CRITICAL** (Credentials & State) | Zero live database files copied; `export_kernel.py` Step 3.6 removes `and_os/var/` from staging entirely. |

---

## 🔄 2. Path & Reference Adaptation Matrix

Before any code is committed or published, the export pipeline must guarantee **zero dangling links** and **zero host coupling**:

1. **Host Path Decoupling:**
   - Absolute path `.` $\to$ `.` (Relative workspace root).
   - Local toolchain paths `~/.gemini/...` $\to$ `~/.gemini/...`.
   - External workspace links (`WORK/pulsar`, `WORK/xcode`) $\to$ `./pulsar`, `./xcode`.
   - Personal cloud volume paths (`./WORK/*`) $\to$ `./pulsar`, `./xcode`, `./WORK` (tilde forms included; catch-all $\to$ `ExternalDrive`).
2. **Identifier Sanitization (AST Cleanliness):**
   - Personal names ("System Architect", "System Architect") $\to$ `"System Architect"`.
   - Studio references ("Studio", "Studio") $\to$ `"Studio"`.
   - Health trackers ("telemetry_sync", "телеметрия") $\to$ `"telemetry_sync"` (valid Python variable identifiers with underscores, not hyphens).
   - Local workstation hostnames (`<your-hostname>.local`) $\to$ placeholder `<your-hostname>.local` in any documentation.
3. **Standalone Integrity (Zero Broken Imports):**
   - `sys_cli.py`: Personal subcommands (`p_health`, `p_telemetry_sync`, `p_fin`) must degrade gracefully without crashing argparse.
   - `quick_verify.py`: Standalone mode must skip Obsidian-vault-only phases (Phase 7 knowledge notes) while preserving strict 100% checks on Phase 0 (Toolchain), Phase 1 (AST Syntax), Phase 2 (Lint), Phase 3 (Clean Code), Phase 4 (Unit Tests), Phase 5 (Secret Scans), and Phase 8 (Rules Freshness). The vault-root hygiene whitelist must include `.git` (a git checkout of the published package legitimately carries VCS metadata at the root).
   - `root_config.py`: Root resolution accepts `system.json` + `and_os/` directory without requiring personal notes.
   - **Deterministic check:** `references/scripts/staged_integrity_audit.py` — every `and_os.*` import in the staged tree must resolve inside the staged tree (AST scan, exit 0 required).

---

## 🛠️ 3. Execution Commands (Step-by-Step DAG)

### Step 1: Execute Deterministic Export & Deep Leak Audit
```bash
and_os/.venv/bin/python3 and_os/bin/export_kernel.py
```
*Expected Outcome:* `✅ 100% AIR-GAP INTEGRITY CONFIRMED: 0 leaks, 0 private paths, 0 credentials.`

### Step 2: Run Hermetic Pre-Flight Verification Inside Staged Repo
```bash
and_os/.venv/bin/python3 and_os/bin/quick_verify.py   # cwd = staged root
```
*Expected Outcome:* `Overall Status : 🟢 ALL PHASES PASSED` (0 critical errors, targeted unit tests passing).  
*Warning:* staging-only green is a **necessary but not sufficient** signal — it cannot see git-checkout-specific defects. Step 7 (Fresh-Clone E2E) is mandatory.

### Step 3: Run SOS Multi-Core Skill Canary Audit
```bash
and_os/.venv/bin/python3 and_os/bin/sys_cli.py skills --probe
```
*Expected Outcome:* `✅ ALL 9 ACTIVE SKILLS VALID, HERMETIC AND HEALTHY!` in $\le 300$ ms.

### Step 4: Verify Root Product Deliverables & FOSS Packaging
Ensure the following files are present and complete in the staged directory root:
- `README.md` (Production-grade showcase, badges, C4 diagram, token benchmarks, quickstart; sample outputs must show **real** measured numbers from the current version, not stale ones).
- `LICENSE` (MIT License).
- `CONTRIBUTING.md` (Clean Code Uncle Bob standard, PR workflow).
- `SECURITY.md` (Air-Gap policy and vulnerability disclosure).
- `.gitignore` — must cover: `__pycache__/`, `*.py[cod]`, `*.db`, `and_os/var/`, `events.jsonl`, `*.lock`, `.DS_Store` (runtime-state completeness gate, §6).
- `pyproject.toml` (PEP 621: name, version, authors, Python `>=3.10`) — **version must equal** `system.json` / `RELEASE_LEDGER.json` / `CHANGELOG.md` (version-alignment gate, §5).
- `CHANGELOG.md` (root level; latest entry first; full published history preserved verbatim — never drop already-public history).
- `system.json` & `and_os/etc/rules_fast_index.json` (machine-readable system specifications).

### Step 5: Deterministic Integrity Audit (Extended Patterns + Import Integrity + Delta)
```bash
python3 and_os/lib/skills/github-ops/references/scripts/staged_integrity_audit.py ~/.and_os/tmp/and-os-core [published-clone-path]
```
*Expected Outcome:* `exit 0` — 0 findings across the 10 extended leak patterns (§7), every `and_os.*` import resolves inside the staged tree, and (when a published clone is given) the changed/new/removed delta readout for user review.

### Step 6: Payload Assembly (Update an Existing Repo)
For a **first release**: `git init -b main` + neutral author + commit (see Step 6a below).  
For an **update to an existing repo** (canonical flow):
```bash
git clone https://github.com/<owner>/<repo>.git <work-clone>     # FULL clone, never shallow
cd <work-clone>
find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +    # wipe non-.git content
rsync -a --exclude='.git' ~/.and_os/tmp/and-os-core/ ./
git add -A
git diff --cached --name-status   # classify A/M/D/R and read to the user (payload purity gate)
```
*Staging purity invariant:* if ANY test was run inside staging after the export, **re-run Step 1 first** — the parity sync (quick_verify Phase 8) re-creates `and_os/var/` and re-projects `RELEASE_LEDGER.json`/`CHANGELOG.md` in the tree under test (§4).

### Step 6a: Clean Git Packaging & Author Metadata Neutralization
```bash
git config user.name "System Architect"
git config user.email "noreply@github.com"
git commit -m "feat(core): <version> — <scope summary>"
```
*Verification Checks:* `git status --porcelain` completely empty (Zero untracked/dirty files); committed-tree artifact scan = 0 (`.pyc` / `__pycache__` / `*.db` / `events.jsonl` / `and_os/var/`).

### Step 7: Fresh-Clone E2E Gate (Mandatory Before Push)
Commit first, then verify the **committed state** from a fresh clone — never from staging:
```bash
git clone https://github.com/<owner>/<repo>.git <e2e-clone> && cd <e2e-clone>
and_os/.venv/bin/python3 and_os/bin/quick_verify.py            # 🟢 ALL PHASES PASSED
and_os/.venv/bin/python3 and_os/bin/sys_cli.py skills --probe  # 100% healthy
and_os/.venv/bin/python3 -m pytest and_os/lib/core -q          # all pass
git ls-tree -r --name-only HEAD | grep -cE '\.pyc|__pycache__|\.db$|events\.jsonl|and_os/var/'   # 0
```
*Rationale:* staging has no `.git` directory; a real checkout does. Any gate that is sensitive to git-checkout structure (root hygiene, ignored-file behavior, parity side effects) can only be validated here. After the run, remove parity side effects from the throwaway clone (`rm -rf and_os/var and_os/etc/CHANGELOG.md`) — they are expected in a foreign checkout (see §9 observation).

### Step 8: Publish via Official GitHub CLI (Requires Explicit Confirmation)
Before this step, present the **approval artifact**: diffstat by change class + full commit message + release notes draft.
```bash
# First release:
/opt/homebrew/bin/gh repo create <owner>/<repo> --public --source=<path> --push --description "<desc>"
# Update + release:
git push origin main        # no force-push, no history rewrite
/opt/homebrew/bin/gh release create <tag> --repo <owner>/<repo> --target main --title "<title>" --notes-file <notes.md>
```
*Tag discipline:* force-move a release tag **only before its first consumption** (no downloads, no CI references, no user pins) AND disclose the re-target in the cycle report; otherwise cut a new tag (`vX.Y.(Z+1)`) and keep the old one immutable.

### Step 9: Post-Publish Verification (Mandatory)
```bash
rm -rf <verify-clone> && git clone https://github.com/<owner>/<repo>.git <verify-clone> && cd <verify-clone>
git log --oneline -1                                # expected head SHA
and_os/.venv/bin/python3 and_os/bin/quick_verify.py # 🟢 ALL PHASES PASSED
git ls-tree -r --name-only HEAD | grep -cE '\.pyc|__pycache__|\.db$|events\.jsonl|and_os/var/'   # 0
/opt/homebrew/bin/gh release view <tag> --repo <owner>/<repo>   # tag, target, published, URL
```

---

## 🧊 4. Staging Purity Invariant

Staging (`~/.and_os/tmp/and-os-core`) is a **disposable export artifact, not a verification environment**:

1. The release-parity sync (invoked by `quick_verify.py` Phase 8 → `verify_release_parity`) writes runtime state into the tree under test: `and_os/var/{system_ledger.db, core_state.db, domain_states.json, events.jsonl}` and re-projects `and_os/etc/RELEASE_LEDGER.json` + `and_os/etc/CHANGELOG.md` (local SQLite seed → date normalized to today, release type re-derived).
2. Therefore: **never rsync/commit from a staging that has been executed.** Any in-staging test run invalidates the staging tree; re-export (Step 1) before assembly (Step 6).
3. Functional verification belongs in Step 7 (fresh clone of the committed state), where parity side effects are contained in a throwaway clone and cleaned before exit.
4. `export_kernel.py` Step 3.6 removes `and_os/var/` from staging as the last defensive step — but it cannot prevent post-export mutations, hence rule 2.

---

## 📐 5. Version Alignment Gate (Rule #55)

One SemVer across all projections, checked **before** staging is frozen:

| Projection | File |
| :--- | :--- |
| Packaging | `pyproject.toml` `[project].version` |
| Runtime manifest | `system.json` |
| Release SSoT | `and_os/etc/RELEASE_LEDGER.json` `activeVersion` |
| Storefront | `CHANGELOG.md` current production version |

*Motivation (real incident):* in the v1.0.0 cycle the storefront `pyproject.toml` was stuck at `9.5.0` while `system.json` already carried `1.0.0` — the drift was caught only by manual inspection.

---

## 🛡️ 6. `.gitignore` Completeness Gate

The published `.gitignore` is the **last line of defense** against runtime-state leakage (the exporter whitelist is the first line). It must cover at minimum:

```gitignore
__pycache__/
*.py[cod]
*.db
and_os/var/
*.db-shm
*.db-wal
*.lock
events.jsonl
.DS_Store
```

*Motivation (real incident):* v9.5.0's `.gitignore` covered `*.db-shm`/`*.db-wal`/`*.lock`/`events.jsonl` but **not** `*.db` — three runtime SQLite databases were published to the public repo.

---

## 🔍 7. Extended Leak Pattern List (Second Scan Layer)

Beyond `export_kernel.py`'s built-in 8 patterns, the deterministic audit (`staged_integrity_audit.py`) scans 10 extended patterns:

| # | Class | Pattern (regex, abbreviated) |
| :---: | :--- | :--- |
| 1 | Tokens / keys | `gh[pousr]_…`, `gho_…`, `AKIA…`, `xox[baprs]-…`, `tt1_…`, JWT `eyJhbGciOi…` |
| 2 | Personal emails | `…@(gmail\|ya\|yandex\|proton\|outlook\|icloud).…` |
| 3 | Local hostnames | `<name>.local` (any workstation hostname) |
| 4 | Home-dir remnants | `/Users/[A-Za-z]+`, `C:\Users` |
| 5 | Personal cloud volume | the personal volume name (product names alone are not personal data — calibrate to the volume) |
| 6 | Health / finance | condition/finance identifiers per current scope |
| 7 | NDA project names | studio project identifiers (per current NDA scope — already-public classes excepted per §8) |

Classes 1–7 are **hard fails** (exit 1).

Review-only classes (reported, never auto-fail — human decision required, immutable-history rule §8):

| Class | Pattern | Rationale |
| :--- | :--- | :--- |
| Vault internals | `task_vault.db`, `.obsidian/`, `checkpoints/`, `vault_shadow`, `~/.and_os/`, `.pulsar_cache` | runtime-path **references inside code** (the tools address these paths on the user's machine); the *files* can never ship — enforced by the whitelist + committed-tree artifact scan, not string matching |
| Production chat / tracker | `mattermost`, `ftrack` | already-public tooling classes since v9.5.0 |

---

## 📜 8. Immutable-History Rule

Public git history is **immutable** (no rewrites, no force-pushes of branches). Before masking or "fixing" a string that already exists in published commits:

1. Check the published tree (`gh api repos/<owner>/<repo>/git/trees/main?recursive=1` + content grep on a clone).
2. If the string is **already public**: masking it only in the new version is inconsistent (history still exposes it) and may break external consumers (e.g. Ftrack project-name matching). Route to an explicit **decision** (keep vs. mask) — record the decision in the cycle report.
3. If the string is **new** (first appearance in this version): it is a *new leak* — fix it in the sanitizer/exporter before assembly, no decision needed.

---

## 🏷️ 9. Tag & Release Discipline

- **Branch history:** never force-pushed, never rewritten.
- **Release tag re-target:** permitted only while the tag is unconsumed (created within the same session, no downloads/CI/user pins) — and always disclosed in the cycle report with the old→new SHA pair.
- **Consumed tag:** keep immutable; cut a new tag (`vX.Y.(Z+1)`) for the corrected state.
- **Release notes:** always via `--notes-file` (never inline in argv); structure = one-line summary → `## Highlights` (bullets) → `## Verification` (gate table with measured results).
- **Post-publish observation (design, not a defect):** `verify_release_parity` re-projects `RELEASE_LEDGER.json` inside a foreign checkout (date → today, type re-derived from the local SQLite seed) — a user running the gate will see a dirty `git status` afterward. Candidate for a future cycle: suppress re-projection in standalone mode (no knowledge vault mounted). I-1 zone (`and_os/lib/core/release_ledger.py`) — not modifiable under kernel immutability.

---
[[Vault|← Vault]]
