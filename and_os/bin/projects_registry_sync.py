#!/usr/bin/env python3
"""
projects_registry_sync.py — External Project Registry Regenerator (SSoT sync).

Regenerates and_os/srv/projects_registry.json from live sources only:
  - canonical OS version from and_os/etc/system.json,
  - fixed brain-cluster island entries (context files verified against disk),
  - Pulsar applications via and_os.lib.pulsar.inspector.PulsarInspector,
  - Xcode projects via and_os.lib.xcode.inspector.XcodeInspector.

The registry is a GENERATED projection — no manual editing. Re-run after any
project or infrastructure change; freshness is verified by manifest_probe
(Ring 3) and by `projects_registry_sync.py verify`.

Language standard (Rule #3): all registry fields are technical English.

Usage:
  projects_registry_sync.py sync      regenerate the registry
  projects_registry_sync.py verify    check freshness (updated <= 30 days)
"""

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VAULT_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(VAULT_ROOT))

from and_os.lib.pulsar.inspector import PulsarInspector  # noqa: E402
from and_os.lib.xcode.inspector import XcodeInspector  # noqa: E402

REGISTRY_PATH = VAULT_ROOT / "and_os" / "srv" / "projects_registry.json"
CANONICAL_PATH = VAULT_ROOT / "and_os" / "etc" / "system.json"
FRESHNESS_DAYS = 30

# Fixed brain-cluster island entries. `domain` is a stable English description
# (canonical: SYSTEM.md domain map). `context_file` / `manifest` are checked
# against disk at build time and fall back to the cluster CONTEXT.md.
ISLAND_ENTRIES = {
    "system": {
        "domain": "OS core, kernel, automation, compiler, CLI",
        "context_file": "and_os/README.md",
        "manifest": "and_os/etc/SYSTEM_MAP.md",
        "path": "and_os",
    },
    "terminal": {
        "name": "AND_Terminal Web GUI Console",
        "domain": "Island 8: autonomous GUI terminal, web control panel (:8099)",
        "context_file": "and_os/opt/terminal/CONTEXT.md",
        "manifest": "and_os/opt/terminal/server.py",
        "path": "and_os/opt/terminal",
    },
    "product": {
        "name": "Product Studio CG Production",
        "domain": "Island 5: studio production, Studio, Ftrack, Mars, Kot",
        "context_file": "Product/CONTEXT.md",
        "manifest": "Product/Projects/Mars/CONTEXT.md",
        "path": "Product",
    },
    "story": {
        "name": "Story Narrative & Books",
        "domain": "Island 4: screenplays, books, narrative design, storyboards",
        "context_file": "Story/CONTEXT.md",
        "manifest": "Story/CONTEXT.md",
        "path": "Story",
    },
    "tabu": {
        "name": "Ta-Bu Startup Incubator",
        "domain": "Island 3: B2B SaaS, bots, product hypotheses, finance",
        "context_file": "Ta-Bu/CONTEXT.md",
        "manifest": "Ta-Bu/CONTEXT.md",
        "path": "Ta-Bu",
    },
    "cg_core": {
        "name": "CG_core Media & Consulting",
        "domain": "Island 2: consulting, studio audits, expert reviews",
        "context_file": "CG_core/CONTEXT.md",
        "manifest": "CG_core/CONTEXT.md",
        "path": "CG_core",
    },
    "clippings": {
        "name": "Clippings Knowledge Base",
        "domain": "Island 1: general knowledge base, clipping, article digests",
        "context_file": "Clippings/CONTEXT.md",
        "manifest": "Clippings/CONTEXT.md",
        "path": "Clippings",
    },
}


def read_canonical_version() -> str:
    """Reads the canonical OS version from the single source manifest."""
    with open(CANONICAL_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle).get("version", "unknown")


def resolve_ref(rel_path: str, fallback: str) -> str:
    """Returns the reference if it exists on disk, otherwise the fallback."""
    if (VAULT_ROOT / rel_path).exists():
        return rel_path
    return fallback


def build_island_entry(project_id: str, spec: dict) -> dict:
    entry = {
        "name": spec.get("name", project_id),
        "domain": spec["domain"],
        "context_file": resolve_ref(spec["context_file"], spec["context_file"]),
        "manifest": resolve_ref(spec["manifest"], spec["context_file"]),
        "status": "ACTIVE",
        "path": spec["path"],
    }
    if project_id == "system":
        entry["name"] = f"AnD os v{read_canonical_version()} Core System"
    return entry


def build_pulsar_entries() -> dict:
    """Builds the Pulsar aggregate entry plus one entry per application."""
    entries = {
        "pulsar": {
            "name": "Pulsar 3D Tooling & Native Workspaces",
            "domain": "Island 7: external dashboards, 3D pipeline, native scripts",
            "context_file": "Nero/pulsar/INDEX.md",
            "manifest": "Nero/pulsar/cg_tool.md",
            "status": "ACTIVE",
            "path": str(PulsarInspector().root),
        }
    }
    for app in PulsarInspector().scan_applications():
        entries[f"pulsar__{app['id']}"] = {
            "name": app.get("name", app["id"]),
            "domain": f"Island 7 app: {app.get('category', 'application')}",
            "context_file": f"Nero/pulsar/{app['dir_name']}/PROJECT.md",
            "manifest": app.get("entrypoint", ""),
            "status": "ACTIVE" if app.get("runtime_valid", True) else "DEGRADED",
            "path": app["path"],
        }
    return entries


def build_xcode_entries() -> dict:
    """Builds the Xcode aggregate entry plus one entry per project."""
    inspector = XcodeInspector()
    entries = {
        "xcode": {
            "name": "Xcode iOS/macOS Game Development",
            "domain": "Island 9: iOS/macOS gamedev, Swift, SpriteKit",
            "context_file": "Nero/xcode/CONTEXT.md",
            "manifest": "Nero/xcode/CONTEXT.md",
            "status": "ACTIVE",
            "path": str(inspector.root),
        }
    }
    for project in inspector.scan_projects():
        entries[f"xcode__{project['id']}"] = {
            "name": project.get("name", project["id"]),
            "domain": f"Island 9 project: {project.get('category', 'application')}",
            "context_file": "Nero/xcode/CONTEXT.md",
            "manifest": "Nero/xcode/CONTEXT.md",
            "status": "ACTIVE" if project.get("swift_valid", True) else "DEGRADED",
            "path": project["path"],
        }
    return entries


def build_registry() -> dict:
    """Assembles the full registry document from live sources."""
    projects = {}
    for project_id, spec in ISLAND_ENTRIES.items():
        projects[project_id] = build_island_entry(project_id, spec)
    projects.update(build_pulsar_entries())
    projects.update(build_xcode_entries())
    return {
        "version": "6.0.0",
        "updated": date.today().isoformat(),
        "generated_by": "and_os/bin/projects_registry_sync.py",
        "projects": projects,
    }


def sync_registry() -> dict:
    """Writes the registry atomically (tmp + rename) and returns it."""
    registry = build_registry()
    tmp_path = str(REGISTRY_PATH) + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(registry, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    os.replace(tmp_path, REGISTRY_PATH)
    return registry


def verify_freshness() -> tuple:
    """Checks registry freshness and self-description."""
    if not REGISTRY_PATH.exists():
        return False, ["registry missing"]
    with open(REGISTRY_PATH, "r", encoding="utf-8") as handle:
        registry = json.load(handle)
    errors = []
    try:
        updated = date.fromisoformat(registry.get("updated", "1970-01-01"))
        age_days = (date.today() - updated).days
        if age_days > FRESHNESS_DAYS:
            errors.append(f"registry stale: updated {updated} ({age_days} days ago)")
    except ValueError as err:
        errors.append(f"invalid updated field: {err}")
    if registry.get("generated_by") != "and_os/bin/projects_registry_sync.py":
        errors.append("registry not generated by projects_registry_sync.py (manual drift?)")
    return len(errors) == 0, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="External project registry sync (SSoT)")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("sync", help="Regenerate and_os/srv/projects_registry.json from live sources")
    sub.add_parser("verify", help="Check registry freshness (<=30 days)")
    args = parser.parse_args()

    if args.action == "sync":
        registry = sync_registry()
        print(f"OK  registry synced: {REGISTRY_PATH}")
        print(f"    projects: {len(registry['projects'])} | updated: {registry['updated']}")
        return 0
    if args.action == "verify":
        ok, errors = verify_freshness()
        if ok:
            print("OK  registry fresh and generator-stamped")
            return 0
        for error in errors:
            print(f"FAIL {error}")
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
