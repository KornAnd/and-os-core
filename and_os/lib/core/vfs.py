#!/usr/bin/env python3
"""
vfs.py — Virtual File System & Path Resolver for AnD os.
Part of AnD os Kernel Core (and_os/lib/core/).

Provides hermetic path resolution, directory standards, and safe root discovery.
Principles: Idempotency (Rule №42), Hermetic Paths (Rule №40/42).
"""

import os
from pathlib import Path

def get_vault_root() -> str:
    """Finds the Obsidian Vault root by searching upward for SYSTEM.md or system.json."""
    cur = os.path.abspath(os.path.dirname(__file__))
    while cur and cur != os.path.dirname(cur):
        if os.path.exists(os.path.join(cur, "SYSTEM.md")) and os.path.exists(os.path.join(cur, "system.json")):
            return cur
        cur = os.path.dirname(cur)
    # Default fallback: 3 levels up from and_os/lib/core
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))

VAULT_ROOT = get_vault_root()
AND_OS_ROOT = os.path.join(VAULT_ROOT, "and_os")

# Standard POSIX / FHS System Directories
DIR_BIN = os.path.join(AND_OS_ROOT, "bin")
DIR_BOOT = os.path.join(AND_OS_ROOT, "boot")
DIR_ETC = os.path.join(AND_OS_ROOT, "etc")
DIR_LIB = os.path.join(AND_OS_ROOT, "lib")
DIR_OPT = os.path.join(AND_OS_ROOT, "opt")
DIR_PROC = os.path.join(AND_OS_ROOT, "proc")
DIR_SBIN = os.path.join(AND_OS_ROOT, "sbin")
DIR_SRV = os.path.join(AND_OS_ROOT, "srv")
DIR_VAR = os.path.join(AND_OS_ROOT, "var")

# Subdirectories
DIR_DB = os.path.join(DIR_VAR, "db")
DIR_LOG = os.path.join(DIR_VAR, "log")
DIR_RUN = os.path.join(DIR_VAR, "run")
DIR_MODULES = os.path.join(DIR_LIB, "modules")
DIR_SKILLS = os.path.join(DIR_LIB, "skills")
DIR_TERMINAL = os.path.join(DIR_OPT, "terminal")

def resolve_path(relative_or_absolute: str) -> str:
    """Safely resolves path relative to VAULT_ROOT if not absolute."""
    if os.path.isabs(relative_or_absolute):
        return os.path.abspath(relative_or_absolute)
    return os.path.abspath(os.path.join(VAULT_ROOT, relative_or_absolute))

def ensure_system_dirs():
    """Ensures all standard runtime and data directories exist."""
    for p in [DIR_VAR, DIR_DB, DIR_LOG, DIR_RUN, DIR_PROC]:
        os.makedirs(p, exist_ok=True)
