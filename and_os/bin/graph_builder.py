#!/usr/bin/env python3
"""
graph_builder.py — Engine of the task graphs generation and orchestration (Execution DAG).
Part of the Task Execution Graph standard (Rule #20).

Generates:
1. Mermaid diagrams for insertion into the Markdown notes (with the subgraphs, the skills, the scripts).
2. The Obsidian Canvas (.canvas) with the automatic calculation of the spatial coordinates (Swimlanes / Groups).
3. Validates the graph for the acyclicity (DAG) and the integrity of the dependencies.

Usage:
  python3 graph_builder.py --test --mermaid
  python3 graph_builder.py --test --canvas "output.canvas"
  python3 graph_builder.py --file input_dag.json --mermaid
  python3 graph_builder.py --file input_dag.json --canvas output.canvas
"""

import argparse
import json
import os
import sys
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Set, Tuple


# ==============================================================================
# Obsidian Canvas color palette
# ==============================================================================
# 1 = Red, 2 = Orange, 3 = Yellow, 4 = Green, 5 = Blue, 6 = Purple
COLOR_MAP = {
    "red": "1",
    "orange": "2",
    "yellow": "3",
    "green": "4",
    "blue": "5",
    "purple": "6",
    "default": "5",
}

SKILL_COLOR_MAP = {
    "ftrack-sync": "5",
    "weeek-hub": "3",
    "document-hub": "4",
    "story-dev": "6",
    "status-report": "1",
    "employee-hub": "2",
    "budget-calculator": "3",
    "cg-article": "6",
    "investor-outreach": "2",
    "clipping-finder": "4",
    "ai-rule": "5",
    "comfyui": "5",
    "system-audit": "1",
    "sync-context": "4",
    "vault-router": "5",
}


# ==============================================================================
# DAG validation and Circuit Breaker
# ==============================================================================
def validate_dag(nodes: List[Dict[str, Any]], check_circuit_breaker: bool = False) -> Tuple[bool, List[str]]:
    """Checks the graph for the nodes existence, the dependencies integrity, the acyclicity and the Circuit Breaker limit."""
    errors = []
    node_ids = set()

    for node in nodes:
        nid = node.get("id")
        if not nid:
            errors.append("A node without the mandatory 'id' field was found")
            continue
        if nid in node_ids:
            errors.append(f"Duplicated node identifier: '{nid}'")
        node_ids.add(nid)

        # Check of the Circuit Breaker rule (maximum 3 iterations for the self-check loops)
        mode = str(node.get("mode", "")).lower()
        pattern = str(node.get("pattern", "")).lower()
        if check_circuit_breaker or mode in ("loop", "evaluator-optimizer", "retry") or pattern in ("loop", "evaluator-optimizer"):
            if mode in ("loop", "evaluator-optimizer", "retry") or pattern in ("loop", "evaluator-optimizer"):
                max_iter = node.get("max_iterations")
                if max_iter is None:
                    errors.append(f"Node '{nid}' uses the 'Loop' (Evaluator-Optimizer) pattern, but the 'max_iterations' field is missing. max_iterations <= 3 is required (Circuit Breaker Rule #20).")
                elif not isinstance(max_iter, int) or max_iter > 3:
                    errors.append(f"Node '{nid}' sets max_iterations={max_iter}, which exceeds the Circuit Breaker limit (maximum 3 iterations before the stop and the escalation to a human).")

    # References check
    adj = defaultdict(list)
    in_degree = defaultdict(int)
    for nid in node_ids:
        in_degree[nid] = 0

    for node in nodes:
        nid = node.get("id")
        deps = node.get("depends_on", [])
        for dep in deps:
            if dep not in node_ids:
                errors.append(f"Node '{nid}' references a non-existent dependency '{dep}'")
            else:
                adj[dep].append(nid)
                in_degree[nid] += 1

    if errors:
        return False, errors

    # Cycle check via the Kahn algorithm (topological sort)
    queue = deque([nid for nid in node_ids if in_degree[nid] == 0])
    visited_count = 0

    while queue:
        curr = queue.popleft()
        visited_count += 1
        for neighbor in adj[curr]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if visited_count != len(node_ids):
        errors.append("A cycle was detected in the graph! The task must be a directed acyclic graph (DAG).")
        return False, errors

    return True, []


# ==============================================================================
# Critical path calculation (Critical Path Method / CPM)
# ==============================================================================
def calculate_critical_path(nodes: List[Dict[str, Any]]) -> Tuple[List[str], Set[Tuple[str, str]], int]:
    """Calculates the longest path (the critical path) in the DAG graph."""
    node_map = {n["id"]: n for n in nodes}
    durations = {n["id"]: int(n.get("duration", 1)) for n in nodes}

    adj = defaultdict(list)
    in_degree = defaultdict(int)
    for nid in node_map:
        in_degree[nid] = 0

    for n in nodes:
        nid = n["id"]
        for dep in n.get("depends_on", []):
            if dep in node_map:
                adj[dep].append(nid)
                in_degree[nid] += 1

    # Topological sort
    queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
    topo_order = []
    while queue:
        curr = queue.popleft()
        topo_order.append(curr)
        for neighbor in adj[curr]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # Dynamic programming for the longest path search
    dist = {nid: durations[nid] for nid in node_map}
    parent = {nid: None for nid in node_map}

    for u in topo_order:
        for v in adj[u]:
            weight = dist[u] + durations[v]
            if weight > dist[v]:
                dist[v] = weight
                parent[v] = u

    if not dist:
        return [], set(), 0

    end_node = max(dist, key=dist.get)
    max_weight = dist[end_node]

    # Path reconstruction
    path = []
    curr = end_node
    while curr is not None:
        path.append(curr)
        curr = parent[curr]
    path.reverse()

    edge_pairs = set()
    for i in range(len(path) - 1):
        edge_pairs.add((path[i], path[i + 1]))

    return path, edge_pairs, max_weight



# ==============================================================================
# Mermaid generator
# ==============================================================================
def generate_mermaid(dag: Dict[str, Any], direction: str = "TD",
                     show_critical_path: bool = False) -> str:
    """Generates a clean Mermaid block with the phase grouping and the optional CPM highlight."""
    title = dag.get("title", "Execution Graph")
    nodes = dag.get("nodes", [])

    # Calculate the critical path if requested
    critical_nodes: Set[str] = set()
    critical_edges: Set[Tuple[str, str]] = set()
    if show_critical_path and nodes:
        cp_path, critical_edges, cp_weight = calculate_critical_path(nodes)
        critical_nodes = set(cp_path)

    lines = [
        "```mermaid",
        f"flowchart {direction}",
        f"    %% {title}",
    ]
    if show_critical_path and critical_nodes:
        lines.append(f"    %% ⚡ Critical Path (weight={cp_weight}): {' → '.join(critical_nodes)}")

    lines += [
        "    classDef skillNode fill:#2d3748,stroke:#4a5568,stroke-width:2px,color:#fff,rx:6px,ry:6px;",
        "    classDef gateNode fill:#2c5282,stroke:#3182ce,stroke-width:2px,color:#fff,rx:10px,ry:10px;",
        "    classDef parallelNode fill:#234e52,stroke:#319795,stroke-width:2px,color:#fff,rx:6px,ry:6px;",
        "    classDef criticalNode fill:#742a2a,stroke:#e53e3e,stroke-width:3px,color:#fff,rx:6px,ry:6px;",
        "    classDef statusWorking fill:#744210,stroke:#d69e2e,stroke-width:2px,color:#fff,rx:6px,ry:6px;",
        "    classDef statusBlocked fill:#742a2a,stroke:#e53e3e,stroke-width:2px,color:#fff,rx:6px,ry:6px;",
        "    classDef statusDone fill:#1c4532,stroke:#38a169,stroke-width:2px,color:#fff,rx:6px,ry:6px;",
    ]

    # Grouping the nodes by the phases
    phases = defaultdict(list)
    for node in nodes:
        phase = node.get("phase", "General steps")
        phases[phase].append(node)

    phase_counter = 1
    for phase_name, p_nodes in phases.items():
        phase_id = f"phase_{phase_counter}"
        phase_counter += 1
        lines.append(f'\n    subgraph {phase_id} ["{phase_name}"]')

        for node in p_nodes:
            nid = node["id"]
            ntitle = node.get("title", nid).replace('"', "'")
            skill = node.get("skill", "")
            script = node.get("script", "")
            src_ref = node.get("src", "") or node.get("src_ref", "")
            dod = node.get("dod", "").replace('"', "'")
            status = str(node.get("status", "")).lower()

            status_icon = ""
            if status == "working":
                status_icon = " 🟡 [WORKING]"
            elif status in ("blocked", "error"):
                status_icon = " 🔴 [BLOCKED]"
            elif status in ("done", "completed", "success"):
                status_icon = " 🟢 [DONE]"

            label_parts = [f"<b>{ntitle}{status_icon}</b>"]
            if skill:
                label_parts.append(f"🎯 <b>{skill}</b>")
            if script:
                label_parts.append(f"⚙️ <code>{script}</code>")
            if src_ref:
                label_parts.append(f"🔍 <i>{src_ref}</i>")
            if dod:
                label_parts.append(f"✅ <i>{dod}</i>")

            label = "<br/>".join(label_parts)
            lines.append(f'        {nid}["{label}"]')

        lines.append("    end")

    # Adding the edges with the critical edges highlight
    lines.append("\n    %% Dependencies (Edges)")
    all_edges = []
    edge_added = False
    for node in nodes:
        nid = node["id"]
        deps = node.get("depends_on", [])
        for dep in deps:
            all_edges.append((dep, nid))
            lines.append(f"    {dep} --> {nid}")
            edge_added = True

    if not edge_added and len(nodes) > 1:
        for i in range(len(nodes) - 1):
            all_edges.append((nodes[i]["id"], nodes[i+1]["id"]))
            lines.append(f"    {nodes[i]['id']} --> {nodes[i+1]['id']}")

    # Applying the node status styles
    lines.append("\n    %% Task status styles (Agent Status Awareness)")
    for node in nodes:
        nid = node["id"]
        status = str(node.get("status", "")).lower()
        if status == "working":
            lines.append(f"    class {nid} statusWorking;")
        elif status in ("blocked", "error"):
            lines.append(f"    class {nid} statusBlocked;")
        elif status in ("done", "completed", "success"):
            lines.append(f"    class {nid} statusDone;")

    # Applying the critical path styles
    if show_critical_path and critical_nodes:
        lines.append("\n    %% Critical path highlight")
        for nid in critical_nodes:
            lines.append(f"    class {nid} criticalNode;")
        for idx, (src, dst) in enumerate(all_edges):
            if (src, dst) in critical_edges:
                lines.append(f"    linkStyle {idx} stroke:#e53e3e,stroke-width:3px;")

    lines.append("```\n")
    return "\n".join(lines)


# ==============================================================================
# Obsidian Canvas (.canvas) generator
# ==============================================================================
def generate_canvas(dag: Dict[str, Any], layout: str = "horizontal",
                    show_critical_path: bool = False) -> Dict[str, Any]:
    """Generates the Obsidian Canvas JSON structure with the automatic grid and the groups calculation."""
    nodes = dag.get("nodes", [])

    # Calculate the critical path if requested
    critical_nodes_set: Set[str] = set()
    critical_edges_set: Set[Tuple[str, str]] = set()
    if show_critical_path and nodes:
        cp_path, critical_edges_set, _ = calculate_critical_path(nodes)
        critical_nodes_set = set(cp_path)
    title = dag.get("title", "Task Execution Graph")

    # Grouping by the phases
    phases = defaultdict(list)
    for node in nodes:
        phase = node.get("phase", "Stage")
        phases[phase].append(node)

    canvas_nodes = []
    canvas_edges = []

    # Card geometry
    CARD_WIDTH = 380
    CARD_HEIGHT = 180
    GAP_X = 140
    GAP_Y = 80
    GROUP_PADDING = 50

    curr_x = 0
    node_positions = {}

    group_idx = 1
    for phase_name, p_nodes in phases.items():
        # Sorting the nodes inside the phase: the parallel tracks
        n_count = len(p_nodes)
        phase_width = CARD_WIDTH + (GROUP_PADDING * 2)
        phase_height = (n_count * CARD_HEIGHT) + ((n_count - 1) * GAP_Y) + (GROUP_PADDING * 2) + 40

        group_id = f"grp_{group_idx}"
        group_idx += 1
        group_y = 0

        # Placing the group
        canvas_nodes.append({
            "id": group_id,
            "type": "group",
            "x": curr_x,
            "y": group_y,
            "width": phase_width,
            "height": phase_height,
            "label": phase_name,
            "color": str((group_idx % 6) + 1),
        })

        # Placing the cards inside the group
        card_x = curr_x + GROUP_PADDING
        card_y = group_y + GROUP_PADDING + 30

        for node in p_nodes:
            nid = node["id"]
            ntitle = node.get("title", nid)
            skill = node.get("skill", "")
            script = node.get("script", "")
            src_ref = node.get("src", "") or node.get("src_ref", "")
            inputs = node.get("inputs", [])
            outputs = node.get("outputs", [])
            dod = node.get("dod", "")
            mode = node.get("mode", "Sequential")
            file_link = node.get("file_link", "")

            # Formation of the card text
            lines = [f"### {ntitle}"]
            if skill:
                lines.append(f"**🎯 Skill:** `{skill}`")
            if script:
                lines.append(f"**⚙️ Script:** `{script}`")
            if src_ref:
                lines.append(f"**🔍 Source Evidence:** `{src_ref}`")
            if mode.lower() in ("parallel", "fork"):
                lines.append("🔀 **Mode:** Parallel")
            if inputs:
                lines.append(f"📥 **In:** {', '.join(inputs)}")
            if outputs:
                lines.append(f"📤 **Out:** {', '.join(outputs)}")
            if dod:
                lines.append(f"✅ **Criterion (DoD):** {dod}")

            text_content = "\n".join(lines)

            # Determination of the color (the critical path overrides the base color)
            color = node.get("color") or SKILL_COLOR_MAP.get(skill, "5")
            if nid in critical_nodes_set:
                color = "1"  # 1 = Red (critical path)

            node_def = {
                "id": nid,
                "type": "text",
                "text": text_content,
                "x": card_x,
                "y": card_y,
                "width": CARD_WIDTH,
                "height": CARD_HEIGHT,
                "color": color,
            }

            if file_link:
                # If a direct note in the vault is specified
                node_def["type"] = "file"
                node_def["file"] = file_link
                del node_def["text"]

            canvas_nodes.append(node_def)
            node_positions[nid] = (card_x, card_y, CARD_WIDTH, CARD_HEIGHT)

            card_y += CARD_HEIGHT + GAP_Y

        curr_x += phase_width + GAP_X

    # Formation of the edges per the JSON Canvas Spec 1.0
    import hashlib
    edge_counter = 1
    for node in nodes:
        nid = node["id"]
        deps = node.get("depends_on", [])
        for dep in deps:
            if dep in node_positions and nid in node_positions:
                # 16-character hex identifier of the edge per the JSON Canvas Spec 1.0 standard
                raw_hash = hashlib.sha256(f"{title}_{dep}_{nid}_{edge_counter}".encode("utf-8")).hexdigest()
                edge_id = raw_hash[:16]
                edge_counter += 1
                edge_def: Dict[str, Any] = {
                    "id": edge_id,
                    "fromNode": dep,
                    "fromSide": "right",
                    "toNode": nid,
                    "toSide": "left",
                    "toEnd": "arrow",
                }
                if (dep, nid) in critical_edges_set:
                    edge_def["color"] = "1"   # red (Preset 1)
                    edge_def["label"] = "⚡ Critical Path"
                canvas_edges.append(edge_def)

    return {
        "nodes": canvas_nodes,
        "edges": canvas_edges,
        "metadata": {
            "version": "1.0-1.0",
            "frontmatter": {
                "title": title,
                "orchestrator": "task-graph",
                "rules": "Rule #20",
            }
        }
    }


# ==============================================================================
# Example of the test complex graph
# ==============================================================================
def get_test_dag() -> Dict[str, Any]:
    """Returns an example of a complex working task with the parallelism."""
    return {
        "title": "Production audit and the delivery of the episode E275 (Mars)",
        "nodes": [
            {
                "id": "step_1",
                "title": "1. The raw Ftrack data export",
                "phase": "Phase 1: The primary data collection",
                "skill": "ftrack-sync",
                "script": "ftrack_sync.py",
                "inputs": ["Ftrack API", "Episode E275"],
                "outputs": ["ftrack_e275_raw.json"],
                "dod": "The data for the 53 shots and the 31 tasks was loaded without errors",
                "mode": "Sequential",
                "depends_on": [],
            },
            {
                "id": "step_2a",
                "title": "2A. The CFX/Animation output analysis",
                "phase": "Phase 2: The parallel analysis",
                "skill": "ftrack-sync",
                "script": "ftrack_report.py",
                "inputs": ["ftrack_e275_raw.json"],
                "outputs": ["Output_E275.md"],
                "dod": "The hours, the overworks and the delay delta were computed",
                "mode": "Parallel",
                "depends_on": ["step_1"],
            },
            {
                "id": "step_2b",
                "title": "2B. The blocker slice on the Weeek board",
                "phase": "Phase 2: The parallel analysis",
                "skill": "weeek-hub",
                "script": "weeek_sync.py",
                "inputs": ["Safari Live Sync", "Mars Board #798"],
                "outputs": ["Weeek_Mars_Blockers.md"],
                "dod": "All the tasks with the Blocked status and the delay >30d were identified",
                "mode": "Parallel",
                "depends_on": ["step_1"],
            },
            {
                "id": "step_2c",
                "title": "2C. The check of the artists roster and the rates",
                "phase": "Phase 2: The parallel analysis",
                "skill": "employee-hub",
                "script": "doc_analyze.py",
                "inputs": ["MARS_STAFF.xlsx"],
                "outputs": ["CFX_Dept_Resources.md"],
                "dod": "The availability of the leads and the supervisors for the finalization was confirmed",
                "mode": "Parallel",
                "depends_on": ["step_1"],
            },
            {
                "id": "step_3",
                "title": "3. The consolidation of the status report and the risks",
                "phase": "Phase 3: The finalization and the release",
                "skill": "status-report",
                "script": "validate_system.py",
                "inputs": ["Output_E275.md", "Weeek_Mars_Blockers.md", "CFX_Dept_Resources.md"],
                "outputs": ["Status_Mars_E275_Final.md"],
                "dod": "The final protocol with the action points and the risk assessment was formed",
                "mode": "Sequential",
                "depends_on": ["step_2a", "step_2b", "step_2c"],
            },
        ]
    }


def generate_vault_index_dag(vault_root: str = ".") -> Dict[str, Any]:
    """Generates the dependency and the links graph of the ANDREY OS subsystems (Graphify Pattern)."""
    return {
        "title": "The links and the subsystems map of ANDREY OS (Graph Index)",
        "description": "Topological graph: Manifests -> Skills -> Scripts -> Projects -> Storage",
        "nodes": [
            {
                "id": "manifests",
                "title": "Manifests and Rules (#0-22)",
                "phase": "Level 0: The architectural core",
                "skill": "system-audit",
                "script": "SYSTEM.md, rules.md, system.json, AGENTS.md",
                "inputs": ["Vault Root"],
                "outputs": ["Session context"],
                "dod": "The Don't Load, Think in Code, DAG, Anti-Slop and Anti-Hallucination rules were loaded",
                "mode": "Sequential",
                "depends_on": [],
            },
            {
                "id": "router",
                "title": "Skill & Vault Routing",
                "phase": "Level 1: Routing",
                "skill": "skill-router",
                "script": "skill-router, vault-router, task-graph",
                "inputs": ["The user request"],
                "outputs": ["Primary Skill + Work mode + Execution DAG"],
                "dod": "The single entry point and the target catalog Nero/ were determined",
                "mode": "Sequential",
                "depends_on": ["manifests"],
            },
            {
                "id": "production_hub",
                "title": "Production and Team (Mars, Kot, Studio)",
                "phase": "Level 2: The domain clusters",
                "skill": "ftrack-sync",
                "script": "ftrack_sync.py, mattermost_sync.py, weeek_sync.py",
                "inputs": ["Ftrack API", "Mattermost", "Weeek"],
                "outputs": ["Shot statuses", "Follow-up meetings", "Budgets"],
                "dod": "The production data was actualized",
                "mode": "Parallel",
                "depends_on": ["router"],
            },
            {
                "id": "docs_hub",
                "title": "The universal document normalizer",
                "phase": "Level 2: The domain clusters",
                "skill": "document-hub",
                "script": "convert_doc.py (MarkItDown), doc_analyze.py, xl_analyze.py",
                "inputs": ["PDF", "XLSX", "DOCX", "PPTX", "Scans"],
                "outputs": ["Clean Markdown for the LLM"],
                "dod": "The document was converted into Markdown with a 70% token saving",
                "mode": "Parallel",
                "depends_on": ["router"],
            },
            {
                "id": "ai_council",
                "title": "AI & Strategic audit (LLM Council)",
                "phase": "Level 2: The domain clusters",
                "skill": "llm-council",
                "script": "ai-rule, prompt-improver, llm-council",
                "inputs": ["Ideas", "Prompts", "Architectural decisions"],
                "outputs": ["The critical verdict", "The generation workflow"],
                "dod": "The stress test without the model sycophancy was performed",
                "mode": "Parallel",
                "depends_on": ["router"],
            },
            {
                "id": "health_hub",
                "title": "The family health and sport (МЕДСИ, telemetry_sync, Ironman)",
                "phase": "Level 2: The domain clusters",
                "skill": "health-diagnostics-hub",
                "script": "telemetry_sync_sync.py, endurance-training-plan",
                "inputs": ["telemetry_sync Connect", "Lab forms", "МЕДСИ"],
                "outputs": ["health_diagnostics.md", "The training microcycle"],
                "dod": "The medical gateway and the load safety were honored",
                "mode": "Parallel",
                "depends_on": ["router"],
            },
            {
                "id": "memory_validation",
                "title": "Memory, Validation and Telemetry",
                "phase": "Level 3: The loop closing",
                "skill": "knowledge-promoter",
                "script": "validate_system.py, sync_context.py, telemetry.md",
                "inputs": ["The execution results"],
                "outputs": ["decision-log", "telemetry.md", "34 CONTEXT.md"],
                "dod": "The system was checked for the 100% integrity and the knowledge was saved in Nero/",
                "mode": "Sequential",
                "depends_on": ["production_hub", "docs_hub", "ai_council", "health_hub"],
            },
        ],
    }


# ==============================================================================
# CLI entry point
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="Task Execution Graph Engine (Rule #20)")
    parser.add_argument("--file", "-f", help="Path to the JSON file with the DAG structure")
    parser.add_argument("--test", action="store_true", help="Use the test reference task graph")
    parser.add_argument("--vault-index", action="store_true", help="Build the graph of the links and the subsystems of ANDREY OS")
    parser.add_argument("--mermaid", action="store_true", help="Print the Mermaid diagram to stdout")
    parser.add_argument("--canvas", help="Path to save the Obsidian Canvas (.canvas) file")
    parser.add_argument("--validate", action="store_true", help="Only check the DAG validity")
    parser.add_argument("--direction", default="TD", choices=["TD", "LR"], help="Mermaid orientation: TD or LR")
    parser.add_argument("--critical-path", action="store_true",
                        help="Calculate and highlight the critical path (CPM, Rule #20)")
    parser.add_argument("--circuit-breaker", action="store_true",
                        help="Check the max_iterations <= 3 field in the Loop nodes (Circuit Breaker, Rule #20)")

    args = parser.parse_args()

    dag_data = None
    if args.vault_index:
        dag_data = generate_vault_index_dag()
    elif args.test:
        dag_data = get_test_dag()
    elif args.file:
        if not os.path.exists(args.file):
            print(f"[ERROR] File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            dag_data = json.load(f)
    elif not sys.stdin.isatty():
        try:
            dag_data = json.load(sys.stdin)
        except Exception as e:
            print(f"[ERROR] Failed to read the JSON from stdin: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(0)

    nodes = dag_data.get("nodes", [])
    valid, errors = validate_dag(nodes, check_circuit_breaker=args.circuit_breaker)

    if not valid:
        print("[DAG VALIDATION ERROR]:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(2)

    if args.validate:
        print(f"✅ DAG '{dag_data.get('title', 'Untitled')}' validated successfully! Nodes: {len(nodes)}, no cycles.")
        return

    # Show the critical path in the console
    show_cp = args.critical_path
    if show_cp and nodes:
        cp_path, _, cp_weight = calculate_critical_path(nodes)
        print(f"⚡ Critical path (CPM, weight={cp_weight}): {' → '.join(cp_path)}\n")

    # Mermaid generation
    if args.mermaid or (not args.canvas and not args.validate):
        mermaid_code = generate_mermaid(dag_data, direction=args.direction,
                                        show_critical_path=show_cp)
        print(mermaid_code)

    # Canvas generation
    if args.canvas:
        canvas_dict = generate_canvas(dag_data, show_critical_path=show_cp)
        os.makedirs(os.path.dirname(os.path.abspath(args.canvas)), exist_ok=True)
        with open(args.canvas, "w", encoding="utf-8") as f:
            json.dump(canvas_dict, f, ensure_ascii=False, indent=2)
        print(f"✅ Canvas file created successfully: {args.canvas} (nodes: {len(canvas_dict['nodes'])}, edges: {len(canvas_dict['edges'])})")


if __name__ == "__main__":
    main()
