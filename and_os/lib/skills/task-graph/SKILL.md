---
name: task-graph
description: "Use when querying the SQLite task index, managing priority blockers, computing dependency DAGs across all vault markdown TODOs, or publishing compiled task DAGs as vertical-slice tickets (local scratch issues or GitHub)."
version: "1.3.0"
lifecycle: ACTIVE
ttl: STATIC
reviewed: 2026-11-15
domain: system
island: 8
context_tier: WORK
facade_binding: "sys_cli"
modality: DECLARATIVE_KNOWLEDGE
allowed-tools: ["Read", "Write", "Bash", "Grep"]
probe_cmd: "python3 and_os/bin/task_db_engine.py --help > /dev/null"
---
## Catalogs
- [[Tasks/CONTEXT|Tasks — backlog and active sprints]]
- [[and_os/lib/skills/ROUTING|ROUTING — skills and domain routing matrix]]
- [[and_os/bin/graph_builder.py|graph_builder.py — DAG graph compilation engine]]
- [[and_os/lib/skills/task-graph/references/TO_TICKETS|TO_TICKETS — vertical-slice tickets specification]]

**Scope:** Universal planning and execution orchestrator for complex multi-step or cross-domain tasks (modes `WORK`, `STRATEGIC`, `SYSTEM`). Implements **Rule №20 (DAG Orchestration)**: non-trivial tasks are never executed blindly in sequence — they are deconstructed into a DAG where each node declares a primary skill, a deterministic script ("Think in Code", Rule №16), IO artifacts, a parallelism swimlane, and a Definition of Done gate.

## Node Contract (8 attributes per node)
1. **ID & Title** — unique identifier (`step_1`, `step_2a`) + concise action.
2. **Phase / Subgraph** — logical milestone container (Ingestion / Analytics / Assembly).
3. **Primary Skill (🎯)** — exactly one skill from the registry (Rule #12 One Primary Skill).
4. **Script (⚙️)** — deterministic tool from `and_os/bin/` (Rule №16); `—` if strictly analytical.
5. **Input & Output (📥📤)** — precise filesystem paths, tables, or APIs.
6. **Execution Mode** — `Sequential` or `Parallel` (independent swimlane branch).
7. **DoD (✅)** — unambiguous empirical validation gate; blocks downstream execution if unmet.
8. **Source Evidence (🔍)** — file/line citation grounding the node's existence; no hallucinated nodes.

## Graph Rules
- **Topology:** pick the minimal pattern that fits the dependencies — Chain (hard dependencies), Fork/Join (independent subtasks), Routing (conditional dispatch), Evaluator-Optimizer loop (iterative refinement). Concurrency only where subtasks are truly independent.
- **Circuit Breaker:** loop nodes must declare `max_iterations ≤ 3`; on limit reached, halt immediately and escalate to the user — never loop unboundedly (autoregressive drift).
  Validation: `python3 and_os/bin/graph_builder.py --file task.json --circuit-breaker`
- **CPM invariant:** compute the critical path (maximum cumulative duration) and unblock/optimize it FIRST — never spend effort on non-blocking peripheral steps.
- **Artifacts (Think in Code):** Mermaid DAG for chat/markdown logs; `.canvas` workspace for multi-day projects:
  - `python3 and_os/bin/graph_builder.py --file task_dag.json --mermaid --critical-path`
  - `python3 and_os/bin/graph_builder.py --file task_dag.json --canvas "Tasks/Plans/task.canvas" --critical-path`

## Execution Pipeline
1. Decompose the prompt into atomic subtasks; isolate hard dependencies from concurrent tracks.
2. Bind each node to exactly one primary skill (`ROUTING.md`) + one deterministic script.
3. Group independent tasks into Fork swimlanes; converge at a Join Gate before downstream progression.
4. Compile the graph artifact (Mermaid and/or `.canvas` via `graph_builder.py`).
5. Execute node by node, validating every node against its explicit DoD.

## Archetypes & Output
Andrey-specific archetype pipelines (animation production / narrative / system audit) and the full Russian output template: `references/dag_templates.md`. Output report (RU): Mermaid graph → ⚡ critical path (A → B → C + total duration) → stage table (Stage | Mode | Skill | Script | Input→Output | DoD) → canvas board path.

## Tickets & Subagent Execution (v1.3)
Publishing a compiled DAG as executable tickets for parallel subagents: tracer-bullet vertical slices (narrow, demoable alone, one fresh context, pre-factoring), blocking edges as `blocked_by`/`blocks`, wide refactors as expand–contract batches, quiz gate before publish; local template `.scratch/<slug>/issues/NN-<slug>.md` in topological order or GitHub via `github-ops` — [[and_os/lib/skills/task-graph/references/TO_TICKETS|TO_TICKETS.md]]. Enforces file contention mutual exclusion across parallel subagents (`MUTUAL_EXCLUSION_REQUIRED`).

## Verification Checklist
- [ ] Graph strictly acyclic; every node carries primary skill, script (where applicable), empirical DoD, and source evidence.
- [ ] Parallel swimlanes explicitly declared; loop nodes enforce `max_iterations ≤ 3`.
- [ ] Critical path calculated and prioritized; graph compiled via Mermaid and/or `.canvas`.
- [ ] Tickets pass 4-question quiz gate; zero file contention between concurrent swimlanes.

## Anti-Triggers & Constraints
- Never execute complex multi-step tasks blindly without generating an execution DAG.
- Never assign non-existent tools, scripts, or skills; never force sequential execution when subtasks are independent.
- A loop node lacking an explicit `max_iterations` bound is a Circuit Breaker violation.
- Do not waste optimization effort on peripheral low-latency tasks instead of the critical path.

## Vault Mutation Protocol (Rule #19 Invariant)
When creating, updating, or patching markdown notes inside the vault:
- DO NOT perform blind raw file overwrites via generic file tools.
- STRICTLY utilize mcp-vault-guard tools (vault_patch, vault_set_frontmatter, vault_read) or microkernel facade:
  python3 and_os/bin/sys_cli.py vault patch --file <path> --find <target> --replace <replacement>
- Ensure zero syntax corruptions in wikilinks (pipe characters) and YAML frontmatter symmetry.
