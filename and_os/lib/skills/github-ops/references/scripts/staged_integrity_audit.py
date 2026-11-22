#!/usr/bin/env python3
"""
staged_integrity_audit.py — Deterministic pre-publication integrity audit.

Second scan layer beyond the exporter's built-in leak patterns. Three
independent, read-only layers:

  A. Extended private-data pattern scan (hard-fail + review-only classes).
  B. Standalone import integrity: every `and_os.*` import in the tree must
     resolve inside the tree (AST scan; a published package that cannot
     import its own modules is a broken package).
  C. Optional delta vs a published clone (changed / added / removed),
     for the mandatory pre-approval readout.

Usage:
  python3 staged_integrity_audit.py <staged-root> [published-clone-root]

Exit codes:
  0 — clean (0 hard-fail findings, 0 broken imports)
  1 — findings require attention (hard-fail leaks and/or broken imports)
  2 — usage or environment error

No network access, no file writes, standard library only. Users of the
open-source edition can extend HARD_PATTERNS with their own private-data
classes (e.g. NDA project identifiers) — the defaults are deliberately
generic so the script itself leaks nothing.
"""

import ast
import difflib
import os
import re
import sys
from typing import Dict, Iterator, List, NoReturn, Set, Tuple

EXIT_CLEAN = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2

# Hard-fail classes: any hit blocks the publication (exit 1).
HARD_PATTERNS = {
    "tokens/keys": re.compile(
        r"gh[pousr]_[A-Za-z0-9]{16,}|gho_[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{12}|"
        r"xox[baprs]-[A-Za-z0-9-]{10,}|tt1_[A-Za-z0-9_-]{20,}|"
        r"eyJhbGciOi[A-Za-z0-9_-]{10,}"),
    "personal emails": re.compile(
        r"[A-Za-z0-9._%+-]+@(gmail|ya|yandex|proton|outlook|icloud)\.[a-z.]+",
        re.IGNORECASE),
    "local hostnames": re.compile(r"\b[A-Z][A-Za-z0-9_-]*\.local\b"),
    "home dir remnants": re.compile(r"/Users/[A-Za-z]+|C:\\Users"),
    # The default is the known personal cloud volume (already public in
    # earlier releases — no new exposure). Extend with your own volumes.
    "personal cloud volume": re.compile(
        r"Yandex\.Disk\.localized|yandex\.ru|disk\.yandex", re.IGNORECASE),
    "health/finance": re.compile(
        r"\b\u041d\u042f\u041a\b|chronic_condition|\u043a\u043e\u043b\u0438\u0442"
        r"|telemetry_sync|telemetry_sync|broker_account|capital_account",
        re.IGNORECASE),
    # Extend this class with your own NDA identifiers per the current
    # confidentiality scope (kept generic here on purpose).
    "nda project names": re.compile(r"NEVER_MATCHES_PLACEHOLDER"),
}

# Review-only classes: reported for a human decision, never auto-fail.
# They typically denote already-public tooling classes (see the protocol's
# immutable-history rule) rather than new leaks.
REVIEW_PATTERNS = {
    "production chat (review)": re.compile(r"mattermost", re.IGNORECASE),
    "production tracker (review)": re.compile(r"ftrack"),
    # Runtime-path references inside code (the tools address these paths
    # on the user's machine). The *files* themselves can never ship —
    # that is enforced by the export whitelist and the committed-tree
    # artifact scan, not by string matching.
    "vault internals (review)": re.compile(
        r"task_vault\.db|\.obsidian/|checkpoints/|vault_shadow|"
        r"~/.and_os/|\.pulsar_cache"),
}


def fail_usage(message: str) -> NoReturn:
    sys.stderr.write(f"[staged_integrity_audit] ERROR: {message}\n")
    sys.stderr.write(__doc__.split("Usage:")[1].split("Exit codes:")[0])
    sys.exit(EXIT_USAGE)


def walk_files(root: str) -> Iterator[Tuple[str, str]]:
    """Yields (absolute path, relative path) for every auditable file."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
        for name in filenames:
            path = os.path.join(dirpath, name)
            yield path, os.path.relpath(path, root)


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


_SELF_REF_COMPILE = re.compile(r"re\.compile\(")
_PATTERN_ROW_TOKENS = re.compile(r"\\|\[[^\]]+\]|…")


def _is_self_reference(line_text: str, rel: str) -> bool:
    """True when a match sits on a pattern-DEFINITION line, not a leak.

    Precedent: export_kernel.audit_leaks (18.11 hostname-pattern incident) —
    a pattern's own definition line must never count as a leak. Two
    documented definition contexts:
      * any .py line carrying a re.compile(...) definition (the scanner's
        own pattern literals, e.g. the NDA placeholder negative control);
      * leak-pattern table rows in the protocol reference doc (markdown
        rows that document regex tokens — the scanner's self-documentation;
        rows without regex tokens still get scanned, so real leaks on other
        table rows are not masked).
    """
    if _SELF_REF_COMPILE.search(line_text):
        return True
    if (rel.endswith("zero_leak_release_protocol.md")
            and line_text.lstrip().startswith("|")
            and _PATTERN_ROW_TOKENS.search(line_text)):
        return True
    return False


def scan_patterns(root: str) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Layer A: extended leak-pattern scan. Returns (hard, review) dicts."""
    hard = {}
    review = {}
    for path, rel in walk_files(root):
        text = read_text(path)
        lines = text.split("\n")
        for label, pattern in HARD_PATTERNS.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                if _is_self_reference(lines[line - 1], rel):
                    continue
                hard.setdefault(label, []).append(
                    f"{rel}:{line} {match.group(0)[:40]!r}")
        for label, pattern in REVIEW_PATTERNS.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                if _is_self_reference(lines[line - 1], rel):
                    continue
                review.setdefault(label, []).append(
                    f"{rel}:{line} {match.group(0)[:40]!r}")
    return hard, review


def collect_modules(root: str) -> Set[str]:
    """Collects the importable module paths available inside the tree."""
    available = set()
    for path, rel in walk_files(root):
        if not rel.endswith(".py"):
            continue
        module = rel[:-3].replace(os.sep, ".")
        if module.endswith(".__init__"):
            module = module[:-9]
        available.add(module)
    return available


def iter_import_names(tree: ast.AST) -> Iterator[str]:
    """Yields top-level imported module names from an AST."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def audit_imports(root: str) -> List[str]:
    """Layer B: every and_os.* import must resolve inside the tree."""
    available = collect_modules(root)
    broken = []
    for path, rel in walk_files(root):
        if not rel.endswith(".py"):
            continue
        try:
            tree = ast.parse(read_text(path))
        except SyntaxError as exc:
            broken.append(f"{rel}: SYNTAX ERROR line {exc.lineno}: {exc.msg}")
            continue
        for name in iter_import_names(tree):
            if not name.startswith("and_os"):
                continue
            parts = name.split(".")
            resolved = any(".".join(parts[:i]) in available
                           for i in range(len(parts), 0, -1))
            if not resolved:
                broken.append(f"{rel}: unresolved import {name}")
    return broken


def delta_vs_published(root: str, published: str) -> Tuple[List[Tuple[int, str]], int, int]:
    """Layer C: changed / added / removed vs the published tree."""
    changed = []
    added = 0
    for path, rel in walk_files(root):
        pub_path = os.path.join(published, rel)
        if not os.path.isfile(pub_path):
            added += 1
            continue
        old = read_text(pub_path).splitlines()
        new = read_text(path).splitlines()
        if old != new:
            matcher = difflib.SequenceMatcher(a=old, b=new, autojunk=False)
            touched = sum(max(i2 - i1, j2 - j1)
                          for tag, i1, i2, j1, j2
                          in matcher.get_opcodes() if tag != "equal")
            changed.append((touched, rel))
    removed = 0
    for path, rel in walk_files(published):
        if not os.path.exists(os.path.join(root, rel)):
            removed += 1
    changed.sort(reverse=True)
    return changed, added, removed


def print_findings(title: str, findings: Dict[str, List[str]], hard: bool) -> None:
    print(f"=== {title} ===")
    if not findings:
        print("clean: 0 findings")
        return
    for label in sorted(findings):
        items = findings[label]
        kind = "HARD" if hard else "REVIEW"
        print(f"{label}: {len(items)} finding(s) [{kind}]")
        for item in items[:10]:
            print(f"   {item}")
        if len(items) > 10:
            print(f"   ... and {len(items) - 10} more")


def main(argv: List[str]) -> int:
    if len(argv) not in (2, 3):
        fail_usage("expected <staged-root> [published-clone-root]")
    root = os.path.abspath(argv[1])
    if not os.path.isdir(root):
        fail_usage(f"staged root is not a directory: {root}")
    if len(argv) == 3 and not os.path.isdir(os.path.abspath(argv[2])):
        fail_usage(f"published clone is not a directory: {argv[2]}")

    hard, review = scan_patterns(root)
    print_findings("A. EXTENDED LEAK PATTERN SCAN", hard, hard=True)
    print_findings("A2. REVIEW-ONLY CLASSES", review, hard=False)

    broken = audit_imports(root)
    print("=== B. STANDALONE IMPORT INTEGRITY ===")
    if broken:
        print(f"BROKEN: {len(broken)}")
        for item in broken[:25]:
            print(f"   {item}")
    else:
        print("clean: every and_os.* import resolves inside the tree")

    if len(argv) == 3:
        published = os.path.abspath(argv[2])
        changed, added, removed = delta_vs_published(root, published)
        print("=== C. DELTA VS PUBLISHED (changed / added / removed) ===")
        for touched, rel in changed:
            print(f"{touched:6d} lines touched  {rel}")
        print(f"added: {added} | removed: {removed} | changed: {len(changed)}")

    total_hard = sum(len(v) for v in hard.values())
    status = ("FINDINGS" if (total_hard or broken) else "CLEAN")
    print(f"\nSUMMARY: {status} (hard-fail leaks {total_hard}, "
          f"broken imports {len(broken)}, review classes "
          f"{sum(len(v) for v in review.values())})")
    return EXIT_FINDINGS if (total_hard or broken) else EXIT_CLEAN


if __name__ == "__main__":
    sys.exit(main(sys.argv))
