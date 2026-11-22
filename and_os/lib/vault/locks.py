#!/usr/bin/env python3
"""
and_os/lib/vault/locks.py — Per-file advisory locks for vault writers.

Exclusive flock on a per-target lock file (and_os/var/locks/), held across a
writer's full read -> validate -> write -> replace cycle. A separate .lock
file is used (not the data file) because os.replace swaps the inode: a lock
held on the data fd would not protect the replacement file.

Mirrors the context_projector lock pattern (Rule #15: Reuse). Lock files are
inert (empty is fine); the directory is safe to empty by hand.

Introduced by audit R-LLM-OBS F6 (21.11): mcp_vault_guard patch /
set_frontmatter / vault_move ran without locks (TOCTOU window under parallel
writers: agents, telemetry_sync_deep_sync cron, vfs_sentinel daemon).
"""

import fcntl
import hashlib
import os

VAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
LOCK_DIR = os.path.join(VAULT_ROOT, "and_os", "var", "locks")


class vault_file_lock:
    """Context manager: exclusive advisory lock for one vault note.

    Usage (single file):
        with vault_file_lock("Nero/note.md"):
            ... read, validate, write tmp, os.replace ...

    Usage (two endpoints, e.g. move — always acquire in sorted order so two
    concurrent operations cannot deadlock):
        with contextlib.ExitStack() as stack:
            for name in sorted({src_rel, dst_rel}):
                stack.enter_context(vault_file_lock(name))
    """

    def __init__(self, rel_path: str):
        os.makedirs(LOCK_DIR, exist_ok=True)
        # sha256 (22.11 audit C-05): derivation of the lock file NAME only —
        # not a cryptographic use — but sha256 keeps the derivation free of
        # weak-hash scanner findings and collision-safe at 16 hex chars.
        # Old sha1-named locks in LOCK_DIR are inert (advisory flock, never
        # matched again; the directory is safe to empty by hand).
        digest = hashlib.sha256(rel_path.encode("utf-8")).hexdigest()[:16]
        self._lock_path = os.path.join(LOCK_DIR, f"vault_{digest}.lock")
        self._fh = None

    def __enter__(self):
        self._fh = open(self._lock_path, "w")
        fcntl.flock(self._fh.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
            self._fh.close()
        finally:
            self._fh = None
        return False
