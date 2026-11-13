#!/usr/bin/env python3
"""
release_pipeline.py — Canonical Release Pipeline (audit R3, F3; R3-VER-1..3).

`sys_cli release bump` delegates to this module. The sequence is strict:
  1. Optional quality gate (quick_verify + Health Grid audit) — read-only
     precondition; a blocking failure aborts the release before ANY state
     change, so no orphan checkpoints are left behind (R3-VER-3).
  2. Pre-release CoW checkpoint (safety net for the transition, R3-VER-2).
  3. Canonical write: and_os/etc/system.json — the SSoT file is the single
     manual write of the whole pipeline.
  4. Root projection: manifest_projector.project_root() — regenerates the
     thin root system.json with a fresh canonical_sha256. The legacy bump
     hand-wrote BOTH files, leaving the hash chain stale (Ring 3 RED until a
     manual re-projection — R3-VER-1).
  5. Ledger: release_ledger.record_release() — SQLite + CHANGELOG.md +
     RELEASE_LEDGER.json + rules fast index (via sync_projections).
  6. Post-release integrity verify — a failure is reported loudly
     (ok=False, exit 1 upstream), never as a silent green release.

Kernel immutability (I-1): release_ledger, manifest_projector and
checkpoint_manager are composed as-is and are never modified here.
"""

import json
import os
import subprocess
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_ROOT = os.path.abspath(os.path.join(_MODULE_DIR, "..", ".."))
BIN_DIR = os.path.join(VAULT_ROOT, "and_os", "bin")
if BIN_DIR not in sys.path:
    sys.path.insert(0, BIN_DIR)

import manifest_projector  # noqa: E402  (bin/ script, path-extended above)


class ReleaseAbortError(Exception):
    """The quality gate failed: the release is aborted, nothing is written."""


def default_checkpoint(vault_root: str, name: str) -> bool:
    """Creates a CoW checkpoint via the real checkpoint_manager (I-1)."""
    from checkpoint_manager import CheckpointManager
    manager = CheckpointManager(vault_root=vault_root)
    return bool(manager.create(name))


def default_quality_gate(vault_root: str) -> Tuple[bool, str]:
    """Runs the two mandatory health gates (quick_verify + Health Grid audit)."""
    py = sys.executable
    quick = subprocess.run(
        [py, os.path.join(BIN_DIR, "quick_verify.py")],
        capture_output=True, text=True, cwd=vault_root, timeout=600,
    )
    if quick.returncode != 0:
        return False, f"quick_verify failed (exit {quick.returncode})"
    audit = subprocess.run(
        [py, os.path.join(BIN_DIR, "sys_cli.py"), "audit"],
        capture_output=True, text=True, cwd=vault_root, timeout=600,
    )
    if audit.returncode != 0:
        tail = (audit.stdout or "").strip().splitlines()[-5:]
        return False, "audit failed: " + " | ".join(tail)
    return True, "quick_verify + audit PASS"


def _default_recorder(spec: Dict[str, Any]) -> None:
    from and_os.lib.core.release_ledger import record_release
    record_release(
        version=spec["version"],
        summary=spec["summary"],
        changes=spec["changes"],
        release_type=spec["release_type"],
        affected_components=spec["components"],
    )


def run_release_pipeline(
    vault_root: str,
    version: str,
    summary: str,
    changes: List[str],
    release_type: str = "MINOR",
    components: str = "core",
    gate: bool = False,
    checkpoint: bool = True,
    checkpoint_fn: Optional[Callable[[str], bool]] = None,
    gate_runner: Optional[Callable[[str], Tuple[bool, str]]] = None,
    projector: Optional[Callable[[], Dict[str, Any]]] = None,
    recorder: Optional[Callable[[Dict[str, Any]], Any]] = None,
    verifier: Optional[Callable[[], Tuple[bool, List[str]]]] = None,
) -> Dict[str, Any]:
    """Executes the canonical release pipeline.

    Returns {"ok": bool, "errors": [...], "log": [...], "version": str}.
    The injectable seams (checkpoint_fn / gate_runner / projector / recorder /
    verifier) exist for the test suite; defaults are the real building blocks.
    """
    log: List[str] = []

    # 1. Quality gate (read-only precondition).
    if gate:
        _gate = gate_runner or default_quality_gate
        passed, detail = _gate(vault_root)
        if not passed:
            raise ReleaseAbortError(f"quality gate failed: {detail}")
        log.append(f"gate: {detail}")

    # 2. Pre-release CoW checkpoint.
    if checkpoint:
        _checkpoint = checkpoint_fn or (lambda name: default_checkpoint(vault_root, name))
        cp_name = f"pre-release-{version}"
        if not _checkpoint(cp_name):
            return {"ok": False, "errors": [f"pre-release checkpoint '{cp_name}' failed — aborted before any write"],
                    "log": log, "version": version}
        log.append(f"checkpoint: {cp_name}")

    # 3. Canonical write — the single manual write (SSoT).
    canonical_path = os.path.join(vault_root, "and_os", "etc", "system.json")
    with open(canonical_path, "r", encoding="utf-8") as handle:
        canonical = json.load(handle)
    old_version = canonical.get("version")
    canonical["version"] = version
    tmp_path = canonical_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(canonical, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    os.replace(tmp_path, canonical_path)
    log.append(f"canonical: {old_version} -> {version}")

    # 4. Root projection — fresh canonical_sha256 (closes R3-VER-1).
    _project = projector or manifest_projector.project_root
    _project()
    log.append("projection: root system.json regenerated")

    # 5. Ledger (kernel, I-1: composed, not modified).
    _record = recorder or _default_recorder
    _record({"version": version, "summary": summary, "changes": changes,
             "release_type": release_type, "components": components})
    log.append("ledger: SQLite + CHANGELOG + RELEASE_LEDGER + fast index")

    # 6. Post-release integrity verify — loud on failure.
    _verify = verifier or (lambda: manifest_projector.verify_projection())
    verified, verify_errors = _verify()
    if not verified:
        log.append(f"verify: FAIL ({len(verify_errors)} error(s))")
        return {"ok": False, "errors": list(verify_errors), "log": log, "version": version}
    log.append("verify: projection integrity OK")
    return {"ok": True, "errors": [], "log": log, "version": version}
