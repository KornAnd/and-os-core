# Interview & Discovery Protocol (Grilling / Office-Hours Gate)

> **Mandatory Reference for `system-architect` (Phase -1 Discovery Gate, v1.2).**  
> Adapted from Matt Pocock's *Grilling* and gstack *Office-Hours* methodologies.  
> **Hard Invariant:** Writing application code, creating skeletons, or drafting `DESIGN_DOC.md` is **prohibited** until the 6 Frontier Questions are answered and locked.

---

## 1. Position in the Lifecycle Pipeline

```
[User Request: "Build new system X"]
       │
       ▼
[Phase -1: Interactive Discovery Interview (Grilling Gate)] ◄─── (Mandatory 6 Frontier Questions)
       │
       ▼ (User answers locked)
[Phase 1: Domain Beacon Mapping & Code Discovery]
       │
       ▼
[Phase 2: DESIGN_DOC.md & ADR Drafting]
       │
       ▼
[Phase 2b: Independent Spec Review Gate (≥ 7/10)]
       │
       ▼
[Phase 3: Runnable Skeleton Scaffolding & Smoke Test]
```

---

## 2. The 6 Frontier Questions (Decision Tree Protocol)

Before drafting any architecture, the agent MUST ask the user **exactly 6 calibrating frontier questions**.

### Question Invariants (All Mandatory):
1. **Frontier-Only:** Ask questions that actually unlock downstream design branches. Never ask trivial questions or ask for information that already exists in the repository.
2. **Explicit Recommendation First:** Every single option must be fully formed, with the agent's recommended choice listed first and prefixed with `(Recommended)`.
3. **Fact-Discovery Pre-Check:** Facts (e.g., existing ports, available SDKs, directory structures) MUST be discovered via `view_file` / `sys_cli` beforehand. Never ask the user to look up system facts the agent can inspect.
4. **Interactive Modal Standard:** In interactive chats, use the standard choice mechanism (`ask_question`). In command-line/unattended runs, default to the `(Recommended)` path while printing the locked decision set.

---

## 3. Canonical 6-Question Matrix

| # | Frontier Dimension | Core Architectural Dilemma | Example Options Format |
|---|-------------------|----------------------------|------------------------|
| **Q1** | **Execution Scope & Boundaries** | What is explicitly IN-SCOPE for v1 vs strictly DEFERRED to v2? | 1. `(Recommended) Core MVP strictly offline-first (Phase 1)`<br/>2. `Full-featured stack with remote sync` |
| **Q2** | **Runtime & Execution Context** | Where does the compute live? | 1. `(Recommended) Detached Python daemon inside and_os (:8080-:8099)`<br/>2. `Native Swift/SpriteKit app in /WORK/xcode/`<br/>3. `ComfyUI custom node extension` |
| **Q3** | **Data Persistence & State** | What is the authoritative state model? | 1. `(Recommended) SQLite / JSON IPC in and_os/var/ (FHS stateless)`<br/>2. `Obsidian Markdown notes via MCP vault-guard`<br/>3. `Purely ephemeral in-memory cache` |
| **Q4** | **Interface & User Interaction** | How does the user interact with the system? | 1. `(Recommended) Git-style CLI facade via sys_cli.py`<br/>2. `Fast Web UI dashboard (:8099 / Pulsar Space)`<br/>3. `Headless background daemon with socket probe` |
| **Q5** | **Failure Handling & Degraded Mode** | How does the system behave when dependencies fail? | 1. `(Recommended) Fail-fast at startup with exit code 1 + diagnostic log`<br/>2. `Graceful degradation on local cached snapshot (Single Active Cache)` |
| **Q6** | **Acceptance DoD (Definition of Done)** | What physical metric proves the implementation succeeded? | 1. `(Recommended) Deterministic smoke test < 200ms with exit 0`<br/>2. `End-to-end integration test with mock fixtures` |

---

## 4. Output: The Locked Decisions Block

Once the user answers (or confirms recommendations), the agent MUST output a locked block:

```markdown
> 🔒 **LOCKED ARCHITECTURAL DECISIONS (Grilling Gate PASSED)**
> 1. Scope: [Answer 1]
> 2. Runtime: [Answer 2]
> 3. State: [Answer 3]
> 4. Interface: [Answer 4]
> 5. Failure Mode: [Answer 5]
> 6. Acceptance DoD: [Answer 6]
```

This block is prepended directly into `docs/DESIGN_DOC.md` under section `1. Context & Locked Invariants`. Scaffolding (Phase 3) is strictly blocked until this receipt is present.
