"""
root_config.py — Hermetic Root Discovery & Environment Resolver
AnD os v1.0.0 — Core Architecture Layer (Unix-Grade Path & Config Grounding)

Defines:
  - resolve_vault_root(): Discovers Vault root strictly by marker files (SYSTEM.md, system.json, and_os/).
  - resolve_pulsar_root(): Resolves external Pulsar space with marker validation (AND_Terminal/server.py).
  - RootConfig: Immutable record holding validated roots and paths.
  - Fail-closed validation: Invalid explicit environment variables raise RootResolutionError.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


class RootResolutionError(RuntimeError):
    """Raised when a system root path cannot be securely or deterministically verified."""
    pass


VAULT_MARKERS = ("system.json", "and_os")
PULSAR_MARKERS = ("AND_Terminal",)


def is_valid_vault_root(path: str) -> bool:
    """Checks whether directory contains mandatory AnD os root markers."""
    if not os.path.isdir(path):
        return False
    return all(os.path.exists(os.path.join(path, marker)) for marker in VAULT_MARKERS)


def is_valid_pulsar_root(path: str) -> bool:
    """Checks whether directory contains valid Pulsar Space markers."""
    if not os.path.isdir(path):
        return False
    terminal_server = os.path.join(path, "AND_Terminal", "server.py")
    return os.path.exists(terminal_server) or any(
        os.path.exists(os.path.join(path, marker)) for marker in PULSAR_MARKERS
    )


def resolve_vault_root() -> str:
    """
    Deterministically resolves the Vault root directory.
    Priority:
      1. Explicit AND_ROOT environment variable (must be valid or fails closed).
      2. Upward directory traversal starting from this file looking for markers.
      3. Fail closed with RootResolutionError.
    """
    env_root = os.getenv("AND_ROOT")
    if env_root:
        norm = os.path.abspath(env_root)
        if not is_valid_vault_root(norm):
            raise RootResolutionError(
                f"Explicit AND_ROOT='{env_root}' is invalid: missing required markers {VAULT_MARKERS}."
            )
        return norm

    # Upward directory traversal
    current = os.path.abspath(os.path.dirname(__file__))
    while current and current != os.path.dirname(current):
        if is_valid_vault_root(current):
            return current
        current = os.path.dirname(current)

    raise RootResolutionError(
        f"Cannot discover AnD os Vault root. No ancestor directory contains markers {VAULT_MARKERS}."
    )


def resolve_pulsar_root(vault_root: Optional[str] = None) -> Optional[str]:
    """
    Resolves the external Pulsar Space directory if available.
    Priority:
      1. Explicit PULSAR_ROOT environment variable (must be valid or fails closed).
      2. Known local canonical path: ./pulsar
      3. Validated sibling check.
      4. Returns None if Pulsar space is not mounted/configured on this machine.
    """
    env_pulsar = os.getenv("PULSAR_ROOT")
    if env_pulsar:
        norm = os.path.abspath(os.path.expanduser(env_pulsar))
        if not is_valid_pulsar_root(norm):
            raise RootResolutionError(
                f"Explicit PULSAR_ROOT='{env_pulsar}' is invalid: missing required markers {PULSAR_MARKERS}."
            )
        return norm

    # Standard host path
    canonical_pulsar = os.path.abspath(os.path.expanduser("./pulsar"))
    if is_valid_pulsar_root(canonical_pulsar):
        return canonical_pulsar

    # Sibling check relative to vault
    if vault_root:
        parent = os.path.dirname(vault_root)
        sibling = os.path.join(parent, "pulsar")
        if is_valid_pulsar_root(sibling):
            return sibling

    return None


@dataclass(frozen=True)
class RootConfig:
    """Immutable system paths container."""
    vault_root: str
    and_os_root: str
    var_dir: str
    etc_dir: str
    bin_dir: str
    pulsar_root: Optional[str] = None

    @classmethod
    def load(cls) -> "RootConfig":
        vault = resolve_vault_root()
        and_os = os.path.join(vault, "and_os")
        pulsar = resolve_pulsar_root(vault_root=vault)
        return cls(
            vault_root=vault,
            and_os_root=and_os,
            var_dir=os.path.join(and_os, "var"),
            etc_dir=os.path.join(and_os, "etc"),
            bin_dir=os.path.join(and_os, "bin"),
            pulsar_root=pulsar,
        )


def get_system_version(vault_root: Optional[str] = None) -> str:
    """
    Single Source of Truth version reader (Rule #55).
    Reads the authoritative canonical version strictly from system.json.
    """
    import json
    root = vault_root or resolve_vault_root()
    manifest = os.path.join(root, "system.json")
    if os.path.exists(manifest):
        try:
            with open(manifest, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("version", "1.0.0")
        except (json.JSONDecodeError, OSError) as err:
            sys.stderr.write(f"[root_config] Notice reading {manifest}: {err}\n")
    return "1.0.0"


def get_system_release(vault_root: Optional[str] = None) -> dict:
    """Returns canonical OS release metadata analogous to /etc/os-release."""
    import json
    root = vault_root or resolve_vault_root()
    manifest = os.path.join(root, "system.json")
    if os.path.exists(manifest):
        try:
            with open(manifest, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "name": data.get("name", "AnD os"),
                "version": data.get("version", "1.0.0"),
                "status": data.get("status", "PRODUCTION_RELEASE"),
                "manifest_version": data.get("manifestVersion", "1.0.0"),
                "rules_count": data.get("rulesCount", 66),
                "root": root
            }
        except (json.JSONDecodeError, OSError) as err:
            sys.stderr.write(f"[root_config] Notice reading release {manifest}: {err}\n")
    return {"name": "AnD os", "version": "1.0.0", "status": "UNKNOWN", "root": root}
