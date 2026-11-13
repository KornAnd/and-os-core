"""Registry and lazy loader of domain subsystems.
Part of AnD os UNIX Git-style CLI architecture.
"""

import importlib
from typing import Dict, Type, Optional
from and_os.bin.cli_subsystems.base import BaseSubsystem

# Domain map: command_name -> module_name, class_name
SUBSYSTEM_MAP: Dict[str, tuple[str, str]] = {
    "track": ("and_os.bin.cli_subsystems.sys_track", "TrackSubsystem"),
    "vault": ("and_os.bin.cli_subsystems.sys_vault", "VaultSubsystem"),
    "proc": ("and_os.bin.cli_subsystems.sys_core", "SystemCoreSubsystem"),
    "status": ("and_os.bin.cli_subsystems.sys_core", "SystemCoreSubsystem"),
    "boot": ("and_os.bin.cli_subsystems.sys_core", "SystemCoreSubsystem"),
    "env": ("and_os.bin.cli_subsystems.sys_core", "SystemCoreSubsystem"),
    "snapshot": ("and_os.bin.cli_subsystems.sys_core", "SystemCoreSubsystem"),
    "notify": ("and_os.bin.cli_subsystems.sys_core", "SystemCoreSubsystem"),
    "vacuum": ("and_os.bin.cli_subsystems.sys_core", "SystemCoreSubsystem"),
    "verify": ("and_os.bin.cli_subsystems.sys_governance", "GovernanceSubsystem"),
    "audit": ("and_os.bin.cli_subsystems.sys_governance", "GovernanceSubsystem"),
    "eval": ("and_os.bin.cli_subsystems.sys_governance", "GovernanceSubsystem"),
    "tdd": ("and_os.bin.cli_subsystems.sys_governance", "GovernanceSubsystem"),
    "sec-audit": ("and_os.bin.cli_subsystems.sys_governance", "GovernanceSubsystem"),
    "rules": ("and_os.bin.cli_subsystems.sys_governance", "GovernanceSubsystem"),
    "cg": ("and_os.bin.cli_subsystems.sys_media", "MediaSubsystem"),
    "comfy": ("and_os.bin.cli_subsystems.sys_media", "MediaSubsystem"),
    "animatic": ("and_os.bin.cli_subsystems.sys_media", "MediaSubsystem"),
    "hybrid-render": ("and_os.bin.cli_subsystems.sys_media", "MediaSubsystem"),
    "consistency": ("and_os.bin.cli_subsystems.sys_media", "MediaSubsystem"),
    "conform": ("and_os.bin.cli_subsystems.sys_media", "MediaSubsystem"),
    "montage": ("and_os.bin.cli_subsystems.sys_media", "MediaSubsystem"),
    "tools": ("and_os.bin.cli_subsystems.sys_dev", "DevSubsystem"),
    "release": ("and_os.bin.cli_subsystems.sys_dev", "DevSubsystem"),
    "checkpoint": ("and_os.bin.cli_subsystems.sys_dev", "DevSubsystem"),
    "clean": ("and_os.bin.cli_subsystems.sys_dev", "DevSubsystem"),
    "mode": ("and_os.bin.cli_subsystems.sys_dev", "DevSubsystem"),
    "handoff": ("and_os.bin.cli_subsystems.sys_dev", "DevSubsystem"),
    "sync-docs": ("and_os.bin.cli_subsystems.sys_dev", "DevSubsystem"),
    "bootstrap": ("and_os.bin.cli_subsystems.sys_dev", "DevSubsystem"),
    "links": ("and_os.bin.cli_subsystems.sys_knowledge_graph", "KnowledgeGraphSubsystem"),
    "context": ("and_os.bin.cli_subsystems.sys_knowledge_graph", "KnowledgeGraphSubsystem"),
    "route": ("and_os.bin.cli_subsystems.sys_knowledge_graph", "KnowledgeGraphSubsystem"),
    "relate": ("and_os.bin.cli_subsystems.sys_knowledge_graph", "KnowledgeGraphSubsystem"),
    "asset": ("and_os.bin.cli_subsystems.sys_knowledge_graph", "KnowledgeGraphSubsystem"),
    "plan": ("and_os.bin.cli_subsystems.sys_knowledge_graph", "KnowledgeGraphSubsystem"),
    "find": ("and_os.bin.cli_subsystems.sys_knowledge_graph", "KnowledgeGraphSubsystem"),
    "doc": ("and_os.bin.cli_subsystems.sys_knowledge_graph", "KnowledgeGraphSubsystem"),
    "dep": ("and_os.bin.cli_subsystems.sys_knowledge_graph", "KnowledgeGraphSubsystem"),
    "pack": ("and_os.bin.cli_subsystems.sys_knowledge_graph", "KnowledgeGraphSubsystem"),
    "telemetry_sync": ("and_os.bin.cli_subsystems.sys_services", "ServicesSubsystem"),
    "health": ("and_os.bin.cli_subsystems.sys_services", "ServicesSubsystem"),
    "finance": ("and_os.bin.cli_subsystems.sys_services", "ServicesSubsystem"),
    "tasks": ("and_os.bin.cli_subsystems.sys_services", "ServicesSubsystem"),
    "vfs": ("and_os.bin.cli_subsystems.sys_services", "ServicesSubsystem"),
    "daemon": ("and_os.bin.cli_subsystems.sys_services", "ServicesSubsystem"),
    "islands": ("and_os.bin.cli_subsystems.sys_services", "ServicesSubsystem"),
    "skills": ("and_os.bin.cli_subsystems.sys_services", "ServicesSubsystem"),
    "skill": ("and_os.bin.cli_subsystems.sys_services", "ServicesSubsystem"),
    "event": ("and_os.bin.cli_subsystems.sys_services", "ServicesSubsystem"),
    "project": ("and_os.bin.cli_subsystems.sys_services", "ServicesSubsystem"),
    "app": ("and_os.bin.cli_subsystems.sys_services", "ServicesSubsystem"),
    "backup": ("and_os.bin.cli_subsystems.sys_services", "ServicesSubsystem"),
    "toolchain": ("and_os.bin.cli_subsystems.sys_services", "ServicesSubsystem"),
    "manifest": ("and_os.bin.cli_subsystems.sys_sot", "SotSubsystem"),
    "registry": ("and_os.bin.cli_subsystems.sys_sot", "SotSubsystem"),
    "fulltext": ("and_os.bin.cli_subsystems.sys_sot", "SotSubsystem"),
    "test": ("and_os.bin.cli_subsystems.sys_testing", "TestingSubsystem"),
}


def get_subsystem(command_name: str) -> Optional[Type[BaseSubsystem]]:
    """Lazily load and return the subsystem class for a given command."""
    if command_name not in SUBSYSTEM_MAP:
        return None
    mod_path, cls_name = SUBSYSTEM_MAP[command_name]
    try:
        mod = importlib.import_module(mod_path)
        return getattr(mod, cls_name)
    except Exception as e:
        import sys
        print(f"Error loading subsystem {command_name}: {e}", file=sys.stderr)
        return None
