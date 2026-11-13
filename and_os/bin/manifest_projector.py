#!/usr/bin/env python3
"""
manifest_projector.py — Root Manifest Projector (Single Source of Truth Guard).

The canonical system manifest lives at and_os/etc/system.json. The vault-root
system.json is a thin GENERATED projection, not a second copy:
  - it keeps root marker discovery working (root_config.VAULT_MARKERS),
  - it satisfies the scalar release contract read by core consumers
    (root_config.get_system_version / get_system_release, release_ledger
    parity check, rules_compiler version read),
  - all content blocks (rules, modules, skills, metadata) exist exclusively
    in the canonical file — zero content duplication, zero drift surface.

Integrity is enforced by the canonical_sha256 field and verified by
manifest_probe (Ring 3) and by `manifest_projector.py verify`.

Usage:
  manifest_projector.py project-root   regenerate the projection
  manifest_projector.py verify         check projection integrity (exit code)
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
VAULT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
CANONICAL_PATH = os.path.join(VAULT_ROOT, "and_os", "etc", "system.json")
ROOT_PATH = os.path.join(VAULT_ROOT, "system.json")

# Scalar release-contract fields mirrored into the root projection.
# Kept in sync with the consumer contract in and_os/lib/core/root_config.py
# (get_system_version / get_system_release) and release_ledger parity check.
MIRRORED_KEYS = ("manifestVersion", "name", "version", "status", "rulesCount")


def sha256_file(path: str) -> str:
    """Computes the SHA-256 digest of a file in streaming chunks."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_canonical() -> dict:
    """Loads the canonical manifest (raises on unreadable/invalid JSON)."""
    with open(CANONICAL_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def build_projection(canonical: dict, canonical_sha: str) -> dict:
    """Builds the thin root projection document from the canonical manifest."""
    projection = {
        "$schema": "and-os-root-projection/v1",
        "root_marker": True,
        "canonical_manifest": "and_os/etc/system.json",
        "canonical_sha256": canonical_sha,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "generated_by": "and_os/bin/manifest_projector.py",
    }
    for key in MIRRORED_KEYS:
        if key in canonical:
            projection[key] = canonical[key]
    return projection


def project_root() -> dict:
    """Regenerates the root projection atomically (tmp + rename)."""
    canonical = load_canonical()
    projection = build_projection(canonical, sha256_file(CANONICAL_PATH))
    tmp_path = ROOT_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(projection, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    os.replace(tmp_path, ROOT_PATH)
    return projection


def verify_projection() -> tuple:
    """Verifies marker, sha256 freshness and mirrored-field parity."""
    try:
        canonical = load_canonical()
    except (OSError, json.JSONDecodeError) as err:
        return False, [f"Canonical manifest unreadable: {err}"]
    try:
        with open(ROOT_PATH, "r", encoding="utf-8") as handle:
            root = json.load(handle)
    except (OSError, json.JSONDecodeError) as err:
        return False, [f"Root projection unreadable: {err}"]

    errors = []
    if root.get("root_marker") is not True:
        errors.append("root_marker missing or not true")
    if root.get("canonical_sha256") != sha256_file(CANONICAL_PATH):
        errors.append("canonical_sha256 stale — re-run 'project-root'")
    for key in MIRRORED_KEYS:
        if key in canonical and root.get(key) != canonical[key]:
            errors.append(f"mirrored field '{key}' drifted: root={root.get(key)!r} canonical={canonical[key]!r}")
    return len(errors) == 0, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Root manifest projection tool (SSoT guard)")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("project-root", help="Regenerate the thin root projection from the canonical manifest")
    sub.add_parser("verify", help="Verify root projection integrity (returns exit code)")
    args = parser.parse_args()

    if args.action == "project-root":
        projection = project_root()
        print(f"OK  root projection written: {ROOT_PATH}")
        print(f"    version={projection.get('version')} canonical_sha256={projection.get('canonical_sha256')[:16]}...")
        return 0
    if args.action == "verify":
        ok, errors = verify_projection()
        if ok:
            print("OK  root projection verified (marker + sha256 + mirrored fields)")
            return 0
        for error in errors:
            print(f"FAIL {error}")
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
