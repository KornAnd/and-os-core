# Zero-Leak Open-Source Release Protocol (Air-Gap Release Standard)

> **Mandatory Reference for `github-ops` Skill (Contour B: Zero-Leak Release Pipeline).**  
> Enforces mathematical data isolation (Rule #57 & Rule #58) and sovereign air-gap integrity when exporting components from AnD os to public GitHub repositories.

---

## 🔒 1. Absolute Blacklist Locks (Vault Air-Gap Red Zone)

The following directories in the Obsidian Vault are **strictly locked** and mathematically excluded from any export or git tracking:

| Directory | Contained Data | Leak Risk | Invariant Enforcement |
| :--- | :--- | :---: | :--- |
| **`Nero/`** | Medical health records (UC/chronic_condition), clinic reports, telemetry_sync biometrics, family, financial ledger, 25 personal life goals. | **CRITICAL** (HIPAA / Privacy) | Hardcoded blacklist in `export_kernel.py`. Automated regex leak pattern scan. |
| **`Product/`, `Studio/`, `Tasks/`** | Studio production NDA (full-length animated features "Kot", "Mars"), artist rates, project sprint tasks. | **CRITICAL** (Commercial NDA) | Never copied to staging. Name sanitization rule replaces studio & project names. |
| **`Ta-Bu/`, `Story/`, `Book/`** | Screenplays, story bibles, book chapters, startup pitch decks & valuation metrics. | **HIGH** (Intellectual Property) | Strictly excluded from whitelist. |
| **`Industry/`, `Clippings/`** | Book summaries, raw research clippings, private enterprise consulting memos. | **MEDIUM** (Client Confidentiality) | Excluded from export whitelist. |
| **`and_os/var/`, `and_os/backups/`** | Live SQLite databases, session tokens, APFS snapshot logs, personal state records. | **CRITICAL** (Credentials & State) | Zero live database files copied; only blank schemas initialized upon startup. |

---

## 🔄 2. Path & Reference Adaptation Matrix

Before any code is committed or published, the export pipeline must guarantee **zero dangling links** and **zero host coupling**:

1. **Host Path Decoupling:**
   - Absolute path `.` $\to$ `.` (Relative workspace root).
   - Local toolchain paths `~/.gemini/...` $\to$ `~/.gemini/...`.
   - External workspace links (`WORK/pulsar`, `WORK/xcode`) $\to$ `./pulsar`, `./xcode`.
2. **Identifier Sanitization (AST Cleanliness):**
   - Personal names ("System Architect", "System Architect") $\to$ `"System Architect"`.
   - Studio references ("Studio", "Studio") $\to$ `"Studio"`.
   - Health trackers ("telemetry_sync", "телеметрия") $\to$ `"telemetry_sync"` (valid Python variable identifiers with underscores, not hyphens).
3. **Standalone Integrity (Zero Broken Imports):**
   - `sys_cli.py`: Personal subcommands (`p_health`, `p_telemetry_sync`, `p_fin`) must degrade gracefully without crashing argparse.
   - `quick_verify.py`: Standalone mode must skip Obsidian-vault-only phases (Phase 7 knowledge notes) while preserving strict 100% checks on Phase 0 (Toolchain), Phase 1 (AST Syntax), Phase 2 (Lint), Phase 3 (Clean Code), Phase 4 (Unit Tests), Phase 5 (Secret Scans), and Phase 8 (Rules Freshness).
   - `root_config.py`: Root resolution accepts `system.json` + `and_os/` directory without requiring personal notes.

---

## 🛠️ 3. Execution Commands (Step-by-Step DAG)

### Step 1: Execute Deterministic Export & Deep Leak Audit
```bash
and_os/.venv/bin/python3 and_os/bin/export_kernel.py
```
*Expected Outcome:* `✅ 100% AIR-GAP INTEGRITY CONFIRMED: 0 leaks, 0 private paths, 0 credentials.`

### Step 2: Run Hermetic Pre-Flight Verification Inside Staged Repo
```bash
~/Documents/Obsidian\ Vault/and_os/.venv/bin/python3 and_os/bin/quick_verify.py
```
*Expected Outcome:* `Overall Status : 🟢 ALL PHASES PASSED` (0 critical errors, 7/7 targeted unit tests passing).

### Step 3: Run SOS Multi-Core Skill Canary Audit
```bash
~/Documents/Obsidian\ Vault/and_os/.venv/bin/python3 and_os/bin/sys_cli.py skills --probe
```
*Expected Outcome:* `✅ ALL 9 ACTIVE SKILLS VALID, HERMETIC AND HEALTHY!` in $\le 300$ ms.

### Step 4: Verify Root Product Deliverables & FOSS Packaging
Ensure the following files are present and complete in the staged directory root:
- `README.md` (Production-grade showcase, badges, C4 diagram, token benchmarks, quickstart).
- `LICENSE` (MIT License).
- `CONTRIBUTING.md` (Clean Code Uncle Bob standard, PR workflow).
- `SECURITY.md` (Air-Gap policy and vulnerability disclosure).
- `.gitignore` (Standard Python/macOS exclusion: `__pycache__`, `*.pyc`, `*.db-wal`, `events.jsonl`, `.DS_Store`).
- `pyproject.toml` (PEP 621 packaging standard: name, version, authors, Python `>=3.10`).
- `system.json` & `and_os/etc/rules_fast_index.json` (Machine-readable system specifications).

### Step 5: Clean Git Packaging & Author Metadata Neutralization
Before running git commands, configure a clean public author to eliminate local workstation hostname leaks (`MacKorn.local`):
```bash
git init -b main
git config user.name "System Architect"
git config user.email "noreply@github.com"
git add .
git commit -m "feat(core): initial open-source release of AnD os microkernel v9.5.0"
```
*Verification Check:* Ensure `git status --porcelain` is completely empty (Zero untracked/dirty files).

### Step 6: Publish via Official GitHub CLI (Requires Explicit Confirmation)
```bash
/opt/homebrew/bin/gh repo create <owner>/<repo> --public --source=<staged-path> --push --description "<concise-description>"
```
