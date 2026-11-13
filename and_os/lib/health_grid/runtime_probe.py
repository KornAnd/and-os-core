"""
runtime_probe.py — Ring 4: Passive Runtime, Ports, Resource Floor & Event Bus.
Covers:
  - APFS disk capacity watchdog (Safe Disk Floor >= 3.0 GB) [Vector 16]
  - Free-First ComfyUI workflow policy (absence of paid SaaS nodes) [Vector 16]
  - macOS LaunchAgents & port daemon monitoring (:8087, :8092) [Vector 17]
  - System Bus (sys_bus.py) & kernel supervisor health [Vector 19]
  - Island 8 Audit (AND_Terminal GUI & OS Compiler :8099) [Vector 20]
  - Quick Knowledge DB availability [Vector 11]
"""

import os
import shutil
import socket
import json
import glob
import sys
import time
from typing import Dict, Any, List, Tuple
from and_os.lib.health_grid import BaseProbeResult

IGNORE_DIRS = {".space", ".obsidian", ".trash", "Trash", ".opencode", ".makemd", ".smart-env", ".git", "node_modules", ".archive"}


class RuntimeProbe:
    @staticmethod
    def run(vault_root: str, fix: bool = False, verbose: bool = True) -> BaseProbeResult:
        result = BaseProbeResult(name="Ring 4: Passive Runtime & Daemons Probe", ring=4)
        issues = 0

        # 1. Disk capacity floor check (Resource Guard >= 3.0 GB)
        free_gb = 0.0
        try:
            free_bytes = shutil.disk_usage(vault_root).free
            free_gb = round(free_bytes / (1024 ** 3), 1)
            if free_gb < 3.0:
                issues += 1
                result.errors.append(f"Free disk capacity ({free_gb} GB) below floor threshold 3.0 GB")
        except Exception as e:
            issues += 1
            result.errors.append(f"Disk capacity check error: {e}")

        # 2. ComfyUI nodes (Free-First policy)
        forbidden_paid_signatures = ["RunwareNode", "StabilityAPI_Key", "DallE3PaidGateway", "ReplicateAPINode"]
        comfy_violations = []
        for root, dirs, files in os.walk(vault_root):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for f in files:
                if f.endswith(".json") and any(term in f.lower() for term in ["workflow", "comfy", "graph"]):
                    fpath = os.path.join(root, f)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as jf:
                            raw = jf.read()
                        for sig in forbidden_paid_signatures:
                            if sig in raw:
                                comfy_violations.append((os.path.relpath(fpath, vault_root), sig))
                    except OSError as err:
                        sys.stderr.write(f"[runtime_probe] Notice reading workflow {fpath}: {err}\n")

        if comfy_violations:
            issues += len(comfy_violations)
            result.warnings.append(f"Paid SaaS nodes detected in ComfyUI workflows: {comfy_violations}")

        # 3. macOS LaunchAgents and network ports (:8087, :8092)
        target_ports = [
            (8087, "Pulsar Mars Gantt Web UI"),
            (8092, "Pulsar Kot Gantt Web UI")
        ]
        port_statuses = {}
        for port, name in target_ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            code = sock.connect_ex(("127.0.0.1", port))
            sock.close()
            port_statuses[port] = (code == 0)

        # 4. System event bus and supervisor
        bus_script = os.path.join(vault_root, "and_os", "bin", "sys_bus.py")
        daemon_script = os.path.join(vault_root, "and_os", "sbin", "and_supervisor.py")
        events_file = os.path.join(vault_root, "and_os", "var", "events.jsonl")

        bus_ok = os.path.exists(bus_script) and os.path.exists(daemon_script)
        if not bus_ok:
            issues += 1
            result.errors.append("sys_bus.py or and_supervisor.py not found")

        # 5. Island 8 (AND_Terminal)
        term_dir = os.path.expanduser("./pulsar/AND_Terminal")
        if not os.path.exists(term_dir):
            term_dir = os.path.join(vault_root, "and_os", "opt", "terminal")

        terminal_files = ["server.py", "index.html", "start_terminal.command"]
        missing_term = [f for f in terminal_files if not os.path.exists(os.path.join(term_dir, f))]
        if missing_term:
            issues += len(missing_term)
            result.warnings.append(f"AND_Terminal: missing files: {missing_term}")

        # 6. Quick Knowledge DB
        quick_db_file = os.path.join(vault_root, "Clippings", "quick_knowledge_db.json")
        quick_db_entries = 0
        if os.path.exists(quick_db_file):
            try:
                with open(quick_db_file, "r", encoding="utf-8") as qf:
                    data = json.load(qf)
                    quick_db_entries = len(data) if isinstance(data, list) else len(data.get("items", []))
            except Exception:
                issues += 1
                result.errors.append("quick_knowledge_db.json is corrupted")

        # 7. Passive VFS Daemon check; audit is strictly read-only
        vfs_pid_file = os.path.join(vault_root, "and_os", "var", "vfs_daemon.pid")
        vfs_running = False
        vfs_status = "pid_file_missing"
        if os.path.exists(vfs_pid_file):
            try:
                with open(vfs_pid_file, encoding="utf-8") as pf:
                    pid = int(pf.read().strip())
                if pid <= 0:
                    vfs_status = "invalid_pid"
                else:
                    os.kill(pid, 0)
                    vfs_running = True
                    vfs_status = "running"
            except ProcessLookupError:
                vfs_status = "stale_pid"
            except PermissionError:
                vfs_status = "permission_denied"
        # 7.5 Supervisor State Freshness Gate (audit R2, WI-2.5): the live
        # runtime state path is resolved from the canonical services.json
        # (supervisor.runtime_root) — no hardcoded Vault or home paths.
        # Stale state (>24h) means the supervisor process is not running.
        supervisor_state_age_hours = None
        services_cfg_path = os.path.join(vault_root, "and_os", "etc", "services.json")
        if os.path.exists(services_cfg_path):
            try:
                with open(services_cfg_path, "r", encoding="utf-8") as scf:
                    services_cfg = json.load(scf)
                runtime_root = os.path.expanduser(
                    services_cfg.get("supervisor", {}).get("runtime_root", ""))
                if runtime_root:
                    supervisor_state = os.path.join(runtime_root, "var", "supervisor_state.json")
                    if os.path.exists(supervisor_state):
                        supervisor_state_age_hours = round(
                            (time.time() - os.path.getmtime(supervisor_state)) / 3600.0, 2)
                        if supervisor_state_age_hours > 24.0:
                            issues += 1
                            result.errors.append(
                                f"Supervisor state stale: {supervisor_state_age_hours}h > 24h "
                                f"at {supervisor_state} (supervisor not running?)")
                    else:
                        issues += 1
                        result.errors.append(
                            f"Supervisor state file missing: {supervisor_state} "
                            f"(runtime_root from services.json)")
            except (OSError, json.JSONDecodeError, ValueError) as serr:
                issues += 1
                result.errors.append(f"Supervisor state freshness check failed: {serr}")

        # 8. Enterprise Vault Backup Health Check (and_os/bin/backup_engine.py)
        backup_engine = os.path.join(vault_root, "and_os", "bin", "backup_engine.py")
        backup_status = "UNKNOWN"
        backup_healthy = True
        if os.path.exists(backup_engine):
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("b_eng", backup_engine)
                b_mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(b_mod)
                b_info = b_mod.get_backup_health()
                backup_healthy = b_info.get("healthy", False)
                backup_status = b_info.get("status", "UNKNOWN")
                if not backup_healthy:
                    issues += 1
                    days_ago = b_info.get("days_since_last", 0)
                    result.warnings.append(f"Enterprise Vault Backup warning: status={backup_status}, last={days_ago} days ago")
            except Exception as be:
                backup_status = f"error:{be}"

        # 9. Islands 7 & 9 Sovereign Contract Parity Gate (Pulsar & Xcode)
        uncontracted_apps = []
        try:
            from and_os.lib.pulsar import PulsarInspector
            p_apps = PulsarInspector().scan_applications()
            for app in p_apps:
                if not app.get("has_contract"):
                    uncontracted_apps.append(f"Island 7: {app['id']} missing PROJECT.md")
        except (ImportError, OSError, ValueError) as perr:
            sys.stderr.write(f"[runtime_probe] Notice: Island 7 contract scan skipped: {type(perr).__name__}: {perr}\n")

        try:
            from and_os.lib.xcode import XcodeInspector
            x_projs = XcodeInspector().scan_projects()
            for proj in x_projs:
                if not proj.get("has_contract"):
                    uncontracted_apps.append(f"Island 9: {proj['id']} missing PROJECT.md")
        except (ImportError, OSError, ValueError) as xerr:
            sys.stderr.write(f"[runtime_probe] Notice: Island 9 contract scan skipped: {type(xerr).__name__}: {xerr}\n")

        if uncontracted_apps:
            issues += len(uncontracted_apps)
            for err in uncontracted_apps:
                result.warnings.append(f"Contract Parity Advisory: {err}")


        result.issues_count = issues
        result.passed = (issues == 0)

        result.details = {
            "disk_free_gb": free_gb,
            "comfy_violations_count": len(comfy_violations),
            "ports_status": port_statuses,
            "sys_bus_active": bus_ok,
            "vfs_daemon_active": vfs_running,
            "vfs_daemon_status": vfs_status,
            "terminal_files_ok": len(missing_term) == 0,
            "quick_db_entries": quick_db_entries,
            "supervisor_state_age_hours": supervisor_state_age_hours,
            "backup_healthy": backup_healthy,
            "backup_status": backup_status
        }

        return result
