"""
graph_probe.py — Ring 1: Relationship Graph, Zero-Orphan Invariant & Inter-Island Highways.
Covers:
  - Wikilink validation for escaped pipes (\\|) [Vector 5]
  - Root directory CONTEXT.md coverage (12/12) [Vector 6]
  - Orphan note indexing and graph connectivity (Zero-Isolation) [Vector 12]
  - 8 logical islands verification and cross-domain highways [Vector 18]
"""

import os
import re
import json
import unicodedata
from collections import defaultdict
from typing import Any, Dict, List, Set, Tuple
from and_os.lib.health_grid import BaseProbeResult

IGNORE_DIRS = {".space", ".obsidian", ".trash", "Trash", ".opencode", ".makemd", ".smart-env", ".git", "node_modules", ".archive", ".archive_versions", ".vault_shadow", "vault_shadow", "backups", "scratch", "tmp", "var"}
HIDDEN_GRAPH_NAMES = {"CONTEXT.md", "context_export.md", "context_lite.md"}


def load_dead_path_config(vault_root: str) -> Dict[str, Any]:
    """Loads the known-dead path config (audit R3, F4). Missing/corrupt file
    degrades to an empty rewrite map (the gate simply has no known-dead set)."""
    path = os.path.join(vault_root, "and_os", "etc", "graph_known_dead_paths.json")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {"rewrites": {}, "severity": "advisory"}


def find_known_dead_refs(broken_links: List[Tuple[str, str]],
                         rewrites: Dict[str, str]) -> List[Tuple[str, str, str]]:
    """Maps broken-link targets onto the known-dead prefixes.

    A dead prefix matches the target itself or the target at a path boundary
    (a prefix followed by '/' or end-of-string), so a longer sibling that
    merely shares the prefix as a string prefix (e.g. '<prefix>2/notes')
    must NOT match. Returns (source, target, replacement).
    """
    refs: List[Tuple[str, str, str]] = []
    for source, target in broken_links:
        for prefix, replacement in rewrites.items():
            if target == prefix or target.startswith(prefix + "/"):
                refs.append((source, target, replacement))
                break
    return sorted(refs)


def scan_known_dead_refs(vault_root: str, rewrites: Dict[str, str]) -> List[Tuple[str, str, str]]:
    """Scans ALL visible Markdown files (routing maps included) and matches
    every wikilink target against the known-dead prefixes.

    The note graph hides two classes of routing regression, so this gate
    must not rely on its broken-link list:
      1. links inside CONTEXT.md maps (HIDDEN_GRAPH_NAMES — those files are
         excluded from the note graph by design, yet they are the primary
         surface where dead routing lives);
      2. links that still resolve via Obsidian short-name semantics after a
         folder move (dead prefix, live file -> counted as resolved).
    Deterministic sorted output; (source, target, replacement) tuples.
    """
    hits: List[Tuple[str, str, str]] = []
    for root, dirs, files in os.walk(vault_root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for filename in files:
            if not filename.lower().endswith(".md"):
                continue
            full_path = os.path.join(root, filename)
            try:
                with open(full_path, "r", encoding="utf-8", errors="strict") as handle:
                    content = handle.read()
            except (OSError, UnicodeError):
                continue
            rel_path = os.path.relpath(full_path, vault_root)
            for raw in re.findall(r"\[\[([^\]\r\n]+)\]\]", content):
                target = raw.split("|", 1)[0].split("#", 1)[0].strip()
                if not target:
                    continue
                matches = find_known_dead_refs([(rel_path, target)], rewrites)
                if matches:
                    hits.extend(matches)
    return sorted(hits)


def load_artifact_excludes(vault_root: str) -> Tuple[str, ...]:
    """Documentation files that intentionally QUOTE the [[| artifact pattern
    (the audit report of record + the append-only telemetry journal) —
    excluded from the defect count. Scope config lives in
    probe_policy.json (probes.graph.artifact_scan_excludes); a missing or
    corrupt policy degrades to no excludes."""
    path = os.path.join(vault_root, "and_os", "etc", "probe_policy.json")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return tuple(data.get("probes", {}).get("graph", {})
                     .get("artifact_scan_excludes", ()))
    except (OSError, ValueError):
        return ()


def load_artifact_severity(vault_root: str) -> str:
    """Severity of the empty-target artifact gate (audit R3, F5(h)).
    Config lives in probe_policy.json (probes.graph.artifact_severity);
    a missing or corrupt policy degrades to advisory, mirroring the
    known-dead path gate (load_dead_path_config)."""
    path = os.path.join(vault_root, "and_os", "etc", "probe_policy.json")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data.get("probes", {}).get("graph", {}).get("artifact_severity", "advisory")
    except (OSError, ValueError):
        return "advisory"


def fix_empty_target_line(line: str) -> str:
    """Deterministic two-rule cleanup of the `[[|` empty-target artifact (R3-DOC-1, F5(h)).

    Rule 1 (unwrap): a closed empty-target construct `[[|<content>]]` is
    replaced by `<content>` — for nested wikilinks this restores the inner
    link, e.g. `[[|[[A|B]]]]` -> `[[A|B]]`.
    Rule 2 (de-prefix): a bare unterminated `[[|` prefix is removed,
    e.g. `[[|- [[A|B]] ...` -> `- [[A|B]] ...`.
    The rules are applied repeatedly (chained wraps) and occurrences inside
    backtick code spans are never touched (documentation may quote the
    pattern). Pure function: the probe module itself stays read-only.
    """
    for _ in range(50):
        pos = None
        in_code = False
        i = 0
        while i < len(line):
            ch = line[i]
            if ch == "`":
                in_code = not in_code
                i += 1
            elif not in_code and line[i:i + 3] == "[[|":
                pos = i
                break
            else:
                i += 1
        if pos is None:
            return line
        depth = 0
        close = None
        i = pos + 3
        while i < len(line):
            if line[i:i + 2] == "[[":
                depth += 1
                i += 2
            elif line[i:i + 2] == "]]":
                if depth == 0:
                    close = i
                    break
                depth -= 1
                i += 2
            else:
                i += 1
        if close is not None:
            line = line[:pos] + line[pos + 3:close] + line[close + 2:]
        else:
            line = line[:pos] + line[pos + 3:]
    return line


def scan_empty_target_artifacts(vault_root: str, excludes: Tuple[str, ...] = ()) -> List[Tuple[str, int]]:
    """Detects the `[[|` empty-target wikilink artifact (R3-DOC-1).

    The graph link regex requires a non-empty target before the pipe, so
    `[[|...` lines are invisible to the broken-link gate; this dedicated
    scan counts them per file (deterministic sorted output). Files listed
    in `excludes` (immutable documentation quoting the pattern) are
    skipped — see load_artifact_excludes.
    """
    found: List[Tuple[str, int]] = []
    for root, dirs, files in os.walk(vault_root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for filename in files:
            if not filename.lower().endswith(".md"):
                continue
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, vault_root)
            if rel_path in excludes:
                continue
            try:
                with open(full_path, "r", encoding="utf-8", errors="strict") as handle:
                    count = sum(1 for line in handle if "[[|" in line)
            except (OSError, UnicodeError):
                continue
            if count:
                found.append((rel_path, count))
    return sorted(found)


def _scan_visible_graph(vault_root: str) -> Dict[str, Any]:
    """Build a fresh, read-only graph from visible Markdown files.

    Determinism contract (audit R2, WI-2.6): on a static tree the returned
    lists are identical across runs — every list is returned in stable
    sorted order, independent of filesystem walk order.

    Explicit definitions:
      isolated  = a visible note with zero resolved incoming AND zero
                  resolved outgoing links (the Zero-Isolation gate target)
      zero_in   = a visible note with zero incoming but at least one
                  outgoing link (contributes to the graph, needs inbound)
      broken    = a wikilink that resolves to zero or >1 candidate files
    """
    nodes: Dict[str, Dict[str, Any]] = {}
    unreadable: List[str] = []
    broken_links: List[Tuple[str, str]] = []
    basename_index: Dict[str, List[str]] = defaultdict(list)

    for root, dirs, files in os.walk(vault_root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for filename in files:
            if not filename.lower().endswith(".md"):
                continue
            full_path = os.path.join(root, filename)
            rel_path = unicodedata.normalize("NFC", os.path.relpath(full_path, vault_root))
            basename = unicodedata.normalize("NFC", filename)
            if basename in HIDDEN_GRAPH_NAMES or basename.lower().startswith("context_"):
                continue
            try:
                with open(full_path, "r", encoding="utf-8", errors="strict") as handle:
                    content = handle.read()
            except (OSError, UnicodeError) as exc:
                unreadable.append(f"{rel_path}: {type(exc).__name__}")
                continue

            raw_targets = re.findall(r"\[\[([^\]\r\n]+)\]\]", content)
            targets = [
                unicodedata.normalize("NFC", target.split("|", 1)[0].split("#", 1)[0].strip()).removesuffix(".md")
                for target in raw_targets
            ]
            nodes[rel_path] = {"directory": os.path.dirname(rel_path), "targets": targets}
            stem = basename[:-3]
            basename_index[stem].append(rel_path)
            basename_index[basename].append(rel_path)
            basename_index[rel_path].append(rel_path)
            basename_index[rel_path[:-3]].append(rel_path)

    incoming: Dict[str, int] = defaultdict(int)
    outgoing: Dict[str, int] = defaultdict(int)
    for source, data in nodes.items():
        for target in data["targets"]:
            normalized = os.path.normpath(target)
            candidates: List[str] = []
            if normalized.startswith("/"):
                normalized = normalized.lstrip("/")
            relative_target = unicodedata.normalize("NFC", os.path.normpath(os.path.join(data["directory"], normalized)))
            if relative_target in nodes:
                candidates = [relative_target]
            elif normalized in nodes:
                candidates = [normalized]
            else:
                candidates = basename_index.get(normalized, [])
                if not candidates:
                    candidates = basename_index.get(os.path.basename(normalized), [])
            resolved = sorted(set(candidates))
            if len(resolved) == 1:
                destination = resolved[0]
                if destination != source:
                    incoming[destination] += 1
                    outgoing[source] += 1
            else:
                broken_links.append((source, target))

    isolated = sorted(path for path in nodes if incoming[path] == 0 and outgoing[path] == 0)
    zero_in = sorted(path for path in nodes if incoming[path] == 0 and outgoing[path] > 0)
    return {
        "total_visible": len(nodes), "isolated": isolated, "zero_in": zero_in,
        "broken_links": sorted(broken_links), "unreadable": sorted(unreadable),
    }


class GraphProbe:
    @staticmethod
    def run(vault_root: str, fix: bool = False, verbose: bool = True) -> BaseProbeResult:
        result = BaseProbeResult(name="Ring 1: Knowledge Graph & Highways Probe", ring=1)

        # 1. Verify root directory CONTEXT.md coverage
        root_dirs = ["Book", "CG_core", "Clippings", "Industry", "Nero", "Product", "Story", "Ta-Bu", "Tags", "Tasks", "and_os", "Studio"]
        missing_context = []
        for rd in root_dirs:
            p = os.path.join(vault_root, rd, "CONTEXT.md")
            if not os.path.exists(p):
                missing_context.append(rd)

        # 2. Check escaped pipes without modifying notes, even if a caller passes fix=True.
        bad_pipe_files = []
        for root, dirs, files in os.walk(vault_root):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for filename in files:
                if not filename.lower().endswith(".md"):
                    continue
                full_path = os.path.join(root, filename)
                try:
                    with open(full_path, "r", encoding="utf-8", errors="strict") as handle:
                        lines = handle.readlines()
                    match_count = sum(
                        len(re.findall(r"\[\[[^\]\r\n]*?\\\|[^\]\r\n]*?\]\]", line))
                        for line in lines
                        if not (line.strip().startswith("|") and line.strip().endswith("|"))
                    )
                    if match_count:
                        bad_pipe_files.append((full_path, match_count))
                except (OSError, UnicodeError):
                    # The graph scan records unreadable files with paths and affects the status.
                    continue

        # 3. Read-only graph scan; never trust a potentially stale report cache.
        graph = _scan_visible_graph(vault_root)
        isolated_orphans = graph["isolated"]
        orphans = graph["zero_in"]
        if graph["broken_links"]:
            result.warnings.append(f"Unresolved wikilinks found: {len(graph['broken_links'])}")
        if graph["unreadable"]:
            result.errors.append(f"Unreadable markdown files: {len(graph['unreadable'])}")

        # 3.1 Known-dead path refs (audit R3, F4; regression guard for the
        # F1/F5 routing fixes). Severity comes from the config: advisory
        # while the F5 cleanup backlog is open, blocking after the vault is
        # clean. Dedicated scan (not the broken-link list): dead routing
        # hides in CONTEXT.md maps and in name-resolvable links after a
        # folder move — both invisible to the note graph.
        dead_cfg = load_dead_path_config(vault_root)
        dead_refs = scan_known_dead_refs(vault_root, dead_cfg.get("rewrites", {}))
        dead_severity = dead_cfg.get("severity", "advisory")
        if dead_refs:
            message = (f"Known-dead path references (fixed routes regressed): "
                       f"{len(dead_refs)} — e.g. {dead_refs[0][1]} -> {dead_refs[0][2]}")
            if dead_severity == "blocking":
                result.errors.append(message)
            else:
                result.warnings.append(message + " [advisory until F5 cleanup]")

        # 3.2 Empty-target wikilink artifact `[[|` (R3-DOC-1; invisible to the
        # link regex, counted here; advisory while the F5 backlog is open).
        # Immutable documentation files quoting the pattern are excluded via
        # the probe policy (scope config, see load_artifact_excludes).
        artifact_excludes = load_artifact_excludes(vault_root)
        artifact_severity = load_artifact_severity(vault_root)
        empty_target_artifacts = scan_empty_target_artifacts(
            vault_root, excludes=artifact_excludes)
        if empty_target_artifacts:
            total_lines = sum(count for _, count in empty_target_artifacts)
            message = (f"Empty-target wikilink artifact '[['|' in "
                       f"{len(empty_target_artifacts)} files ({total_lines} lines)")
            if artifact_severity == "blocking":
                result.errors.append(message)
            else:
                result.warnings.append(message + " [advisory]")

        # 4. Check inter-island highways (Zero-Isolation Integrity)
        required_islands = [
            ("Clippings/CONTEXT.md", "Island 1 (Universal Knowledge Base)"),
            ("CG_core/CONTEXT.md", "Island 2 (Consulting & Media)"),
            ("Ta-Bu/CONTEXT.md", "Island 3 (Startup Incubator)"),
            ("Story/CONTEXT.md", "Island 4 (Narrative & Books)"),
            ("Product/CONTEXT.md", "Island 5 (Studio Production)"),
            ("Nero/CONTEXT.md", "Island 6 (Creator Profile & Health)"),
            ("Nero/pulsar/INDEX.md", "Island 7 (Pulsar & 3D Tooling)"),
            ("and_os/opt/terminal/CONTEXT.md", "Island 8 (Terminal & OS Compiler)"),
            ("Nero/xcode/CONTEXT.md", "Island 9 (Mobile App & Game Engineering)")
        ]

        island_issues = 0
        missing_passports = []
        missing_highways = []

        for rel_path, name in required_islands:
            full_p = os.path.join(vault_root, rel_path)
            if not os.path.exists(full_p):
                island_issues += 1
                missing_passports.append(f"{rel_path} (file not found)")
                continue

            try:
                with open(full_p, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                # Tokens checked with unicode escapes for localized variations
                island_tokens = ["\U0001f3dd\ufe0f **\u041e\u0441\u0442\u0440\u043e\u0432:**", "\U0001f3dd\ufe0f **\u041e\u0441\u0442\u0440\u043e\u0432**", "🏝️ **Island**", "🏝️ **Island:**"]
                highway_tokens = ["🌉", "\u0421\u043c\u0435\u0436\u043d\u044b\u0435 \u043e\u0441\u0442\u0440\u043e\u0432\u0430", "\u041a\u0440\u043e\u0441\u0441-\u043c\u043e\u0441\u0442\u044b", "Highways"]
                if not any(token in content for token in island_tokens):
                    island_issues += 1
                    missing_passports.append(rel_path)
                if not any(token in content for token in highway_tokens):
                    island_issues += 1
                    missing_highways.append(rel_path)
            except Exception as e:
                island_issues += 1
                missing_passports.append(f"{rel_path} ({e})")

        # 5. Gate uses the current scan, independent of cache existence or age.
        isolated_count = len(isolated_orphans)
        if isolated_count > 0:
            result.warnings.append(f"Isolated notes require domain classification; gate does not block them ({isolated_count} items)")

        total_issues = len(missing_context) + len(bad_pipe_files) + island_issues + len(graph["unreadable"])
        result.issues_count = total_issues
        result.passed = (total_issues == 0)

        result.details = {
            "context_coverage": f"{len(root_dirs) - len(missing_context)}/{len(root_dirs)}",
            "visible_markdown_count": graph["total_visible"],
            "missing_context_dirs": missing_context,
            "unresolved_wikilinks": len(graph["broken_links"]),
            "unreadable_markdown": graph["unreadable"],
            "broken_pipe_links": len(bad_pipe_files),
            "fix_requested_but_not_applied": bool(fix and bad_pipe_files),
            "isolated_orphans": isolated_count,
            "orphan_notes_count": len(orphans),
            "island_passports_missing": len(missing_passports),
            "island_highways_missing": len(missing_highways),
            "known_dead_refs": len(dead_refs),
            "known_dead_severity": dead_severity,
            "empty_target_artifact_files": len(empty_target_artifacts),
            "empty_target_artifact_severity": artifact_severity
        }

        if missing_context:
            result.errors.append(f"Missing CONTEXT.md in: {', '.join(missing_context)}")
        if island_issues:
            result.errors.append(f"Inter-island highway defects: {len(missing_passports) + len(missing_highways)}")
        if bad_pipe_files:
            result.warnings.append(f"Files with broken escaped pipes: {len(bad_pipe_files)}")
            if fix:
                result.warnings.append("Fixes not written: GraphProbe is strictly read-only")

        return result
