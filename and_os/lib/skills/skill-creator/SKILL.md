---
name: skill-creator
description: "Use when creating, validating, linting, or updating skills in AnD os. Enforces SKILL_MODULE_ABI v2.1, 8-Island architectural binding, clean code standards (0 silent excepts, depth at most 4), and atomic synchronization across all system manifests."
version: "1.0.0"
lifecycle: ACTIVE
ttl: VOLATILE
reviewed: 2026-11-11
domain: system
island: 8
context_tier: WORK
facade_binding: "sys_cli"
modality: EXECUTABLE_ENGINE
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob"]
probe_cmd: "python3 and_os/lib/skills/skill-creator/scripts/validate_skill.py and_os/lib/skills/skill-creator"
---

# Skill Creator & Architectural Validator (Ring 0 Meta-Skill)

A canonical meta-skill for creating and validating modular skills across the **AnD os v1.0.0** ecosystem.

## 1. Architectural Intent & Scope
- **Classification**: Ring 0 Core Meta-Skill.
- **Governing Standard**: Mandatory compliance with `clean-code-guardian` (`and_os/lib/skills/clean-code-guardian/SKILL.md`) and Uncle Bob engineering protocol.
- **Governing Rules**: Rules #3 (Dual-Language), #8 (Skills Storage), #12 (One Primary Skill), #35/#36 (Dev Protocol & Clean Code), #40 (Semantic Naming), #50 (Stateless Unix FHS), #51 (Bus Decoupling), #54 (Holistic Component Binding), #55 (Single SemVer Invariant).
- **Dual Language Protocol (Rule #3)**:
  - All responses, questions, and conversational output to the user: **strictly Russian**.
  - All skill definitions, code, comments, docstrings, and error messages: **strictly English**.

## 2. Mandatory Engineering Standard (clean-code-guardian Integration)
Every script, engine, and runner generated or modified for any skill MUST strictly adhere to the 3-phase engineering discipline established in `clean-code-guardian`:

1. **Phase 1: First Make it Work**
   - **Boundary Discipline**: Validate inputs at boundary entrypoints (`--json`, `--out`).
   - **Data Shape First**: Model dataclasses and interfaces before writing execution algorithms.
   - **Idempotence**: All file writes and mutations must be strictly idempotent.
2. **Phase 2: Then Make it Right (Anti-Band-Aid Invariant)**
   - **Zero Silent Exceptions**: NEVER wrap failing logic in `try: ... except: pass`. Every exception must log to `sys.stderr` or raise a domain error with actionable diagnostic context.
   - **Complexity & Nesting Control**: Maximum cyclomatic indentation $\le 3$ for business algorithms ($\le 4$ for top-level dispatchers).
   - **Stateless Isolation (Rule #50)**: Never write cache, databases, or runtime state inside the skill folder. State writes belong strictly to `and_os/var/` or via `ClosedLoopDispatcher`.
3. **Phase 3: Follow Practice**
   - **APFS Zero-Cost Protection**: Take shadow snapshot (`sys_cli.py snapshot shadow`) before touching system code.
   - **Canary Test Contract**: Every `EXECUTABLE_ENGINE` skill MUST provide a smoke canary test in `scripts/canary.py` running in $< 500$ ms.

## 3. Creation Workflow (4-Phase Lifecycle)

### Phase 1: Intent & Architectural Coordinate
Determine from user requirements or conversation context:
1. **Name**: lowercase kebab-case (e.g. `blender-render-guard`).
2. **Modality**:
   - `EXECUTABLE_ENGINE`: requires executable Python logic in `scripts/`.
   - `DECLARATIVE_KNOWLEDGE`: requires structured markdown references in `references/`.
3. **Island Binding (1..8)**: identify which Island owns this domain.
4. **Trigger Definition**: observable action beginning strictly with `Use when...`.

### Phase 2: Template Instantiation & Code Generation
- Create directory `and_os/lib/skills/<skill-name>/`.
- Generate `SKILL.md` with complete frontmatter conforming to `SKILL_MODULE_ABI_SPEC.md`.
- If `EXECUTABLE_ENGINE`: generate `scripts/` with zero silent exceptions (`except Exception: pass` is prohibited) and nesting depth $\le 4$.

### Phase 3: Automated Linter & Code Hygiene Gate
Run structural and AST validation:
```bash
python3 and_os/lib/skills/skill-creator/scripts/validate_skill.py and_os/lib/skills/<skill-name>
python3 and_os/lib/skills/skill-creator/scripts/check_code_hygiene.py and_os/lib/skills/<skill-name>
```

### Phase 4: Atomic Mesh Synchronization (Zero Orphans)
Execute atomic registration:
```bash
python3 and_os/lib/skills/skill-creator/scripts/sync_system_mesh.py <skill-name> <island_id>
```
This automatically:
- Creates symlink `.opencode/skills/<skill-name>`
- Registers skill in `and_os/lib/skills/REGISTRY.md`
- Synchronizes total count in `system.json`, `SYSTEM.md`, `SYSTEM_MAP.md`, `SYSTEM_ARCHITECTURE_GRAPH.md`, `README.md`, and `AGENTS.md`.

## 3. Verification Protocol
After creation, always verify system health:
```bash
python3 and_os/bin/sys_cli.py audit --deep
```
Ring 3.5 (Skill Operating Stack) must report **🟢 OK**.

## Vault Mutation Protocol (Rule #19 Invariant)
When creating, updating, or patching markdown notes inside the vault:
- DO NOT perform blind raw file overwrites via generic file tools.
- STRICTLY utilize mcp-vault-guard tools (vault_patch, vault_set_frontmatter, vault_read) or microkernel facade:
  python3 and_os/bin/sys_cli.py vault patch --file <path> --find <target> --replace <replacement>
- Ensure zero syntax corruptions in wikilinks (pipe characters) and YAML frontmatter symmetry.
