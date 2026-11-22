"""
mutation_canary.py — Filesystem mutation canary for probe/audit runs.

Implements the testable invariant "audit runs write nothing outside the
sanctioned volatile zones" (22.11 external audit C-01/C-03). One canary
serves two callers:
  * BinSmokeProbe — wraps Tier B/C: an rc=0 writer (e.g. the 22.11
    passport_sync --help incident) is exactly what the rc-based tiers
    cannot see; the canary sees the filesystem, not the exit code.
  * validate_system.run_full_grid_audit — wraps the whole grid.

Pure and stateless: no logging, no cache (Rule #72: no new data channel).
Exclusions are volatile zones sanctioned by Rule #50 + OS/desktop noise;
every exclusion is listed here (data, auditable).
"""

import os

# Volatile by design (Rule #50): probe caches, reports, trash, venv runtime.
EXCLUDED_DIRS = ("and_os/var", ".trash", "and_os/.venv", ".git")
# Desktop/OS noise that Finder or the kernel may touch at any moment.
EXCLUDED_FILES = (".DS_Store",)
# Obsidian application state: the running app rewrites workspace and plugin
# files (e.g. .makemd/superstate.mdc) at any moment while the user is at the
# machine (22.11: canary hit mid-audit; same noise class as .DS_Store).
EXCLUDED_DIRS = EXCLUDED_DIRS + (".obsidian", ".makemd")


def snapshot(vault_root: str) -> dict:
    """{relpath: (mtime_ns, size)} over vault_root, exclusions pruned."""
    state = {}
    for root, dirs, files in os.walk(vault_root):
        rel_root = os.path.relpath(root, vault_root)
        pruned = []
        for d in dirs:
            rel_d = os.path.normpath(os.path.join(rel_root, d))
            if rel_d in EXCLUDED_DIRS:
                continue
            pruned.append(d)
        dirs[:] = pruned
        for name in files:
            if name in EXCLUDED_FILES:
                continue
            full = os.path.join(root, name)
            rel = os.path.normpath(os.path.relpath(full, vault_root))
            try:
                st = os.stat(full)
            except OSError:
                continue
            state[rel] = (st.st_mtime_ns, st.st_size)
    return state


def compare(before: dict, after: dict) -> dict:
    """Diff two snapshots: added / removed / modified relpaths."""
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    modified = sorted(
        p for p in set(before) & set(after) if before[p] != after[p]
    )
    return {"added": added, "removed": removed, "modified": modified}


def is_clean(report: dict) -> bool:
    return not (report["added"] or report["removed"] or report["modified"])
