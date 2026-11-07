---
name: clean-code-guardian
description: "Use when authoring, reviewing, or refactoring Python code to enforce Uncle Bob clean architecture, zero silent exceptions, and low nesting."
version: "2.0.0"
lifecycle: ACTIVE
domain: system
island: 8
context_tier: QUICK
facade_binding: "sys_cli"
modality: DECLARATIVE_KNOWLEDGE
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob"]
probe_cmd: "test -d and_os/lib/skills/clean-code-guardian"
---
# Clean Code Guardian (Uncle Bob / AnD os Engineering Standard)

Whenever authoring, editing, or refactoring code across AnD os (`and_os/`), Pulsar (`Pulsar_Apps/`), or CG tooling (`cg_workspace/`), follow this 3-phase engineering discipline:

## Phase 1: First Make it Work

### 1. Laziness Protocol & Single Source of Truth
- One architectural decision lives in exactly one place.
- Ship the smallest verified edit that solves the problem. Never refactor surrounding working code unless tasked.

### 2. Foundational Thinking & Data Shape
- Model the data shape and interfaces *before* writing execution logic.
- Make illegal domain states unrepresentable in the type structure.
- If concurrent or asynchronous processes share state, do not share mutable references.

### 3. Dual-Channel Verification (TDD & Smoke Contracts)
- **For Core System Code (`and_os/lib/`, `sbin/`, parsers, data models):**
  - Follow strict TDD: Write the failing test first, see it fail for the expected reason, write minimal code to pass, refactor.
- **For 3D / ComfyUI / VFX / Heavy Neural Tooling:**
  - Enforce **Smoke & Schema Contracts**: verify JSON-graph topology, tensor/payload schemas, and API imports before attempting runtime integration.

### 4. Boundary Discipline & Idempotence
- Validate inputs at the boundary where data enters the module. Inside the module, trust clean data.
- Keep business logic in pure, deterministic functions.
- All mutating operations (file writes, database entries, migrations) must be **strictly idempotent** — running them multiple times produces the exact same state without errors.

---

## Phase 2: Then Make it Right

### 1. Root Cause Elimination (Anti-Band-Aid Invariant)
- Reproduce the failure first.
- Fix the root cause in the architecture.
- **Strictly Forbidden:** Never wrap failing code in silent `try: ... except: pass` blocks or add guards that only mask symptoms.

### 2. Nesting & Complexity Control
- Avoid deep nesting (maximum 3 levels of indentation for business functions).
- Decompose complex workflows into single-responsibility helpers.
- Keep CLI dispatchers cleanly separated from business algorithms.

### 3. Refactoring Discipline
- Pin the existing behavior with tests or baseline assertions.
- Change the internal structure.
- Prove that observable behavior did not change.

---

## Phase 3: Follow Practice

### 1. Guard the Context Window
- Do not dump hundreds of lines of code or raw output into the chat.
- Keep execution logs compact; summarize test results and AST audit status.

### 2. APFS Zero-Cost Protection
- Before touching core system files or user data, ensure an APFS shadow snapshot exists via `sys_cli.py snapshot shadow`.

### 3. Mandatory Telemetry Registration (Rule #11)
- Log all code changes, test verifications, and refactoring passes into `and_os/lib/skills/telemetry.md`.

## Vault Mutation Protocol (Rule #19 Invariant)
When creating, updating, or patching markdown notes inside the vault:
- DO NOT perform blind raw file overwrites via generic file tools.
- STRICTLY utilize mcp-vault-guard tools (vault_patch, vault_set_frontmatter, vault_read) or microkernel facade:
  python3 and_os/bin/sys_cli.py vault patch --file <path> --find <target> --replace <replacement>
- Ensure zero syntax corruptions in wikilinks (pipe characters) and YAML frontmatter symmetry.
