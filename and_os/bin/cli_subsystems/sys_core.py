"""System Core subsystem (proc, status, boot, env, snapshot, vacuum, notify).
Modular extraction from sys_cli.py following UNIX & Clean Architecture principles.
Covers virtual procfs (/proc), liveness probes, environment runtime maps, and APFS snapshots.
"""

import os
import sys
from typing import Any
from and_os.bin.cli_subsystems.base import BaseSubsystem, run_script, auto_log_telemetry, VAULT_ROOT


class SystemCoreSubsystem(BaseSubsystem):
    name = "system_core"
    description = "Core OS diagnostics, /proc telemetry, snapshots, status, and runtimes"

    @classmethod
    def register_subparsers(cls, subparsers) -> None:
        # Status probe
        p_status = subparsers.add_parser("status", help="Deep factual health check and liveness probes of the services (UNIX probe)")
        p_status.add_argument("--json", action="store_true", help="JSON output")

        # Boot init
        p_boot = subparsers.add_parser("boot", help="Fast system start and the readiness screen (Runlevel 5 Init)")
        p_boot.add_argument("--no-notify", action="store_true", help="Do not send the quiet macOS notification")

        # Proc telemetry
        p_proc = subparsers.add_parser("proc", help="Virtual telemetry space /proc (0-Token Reading)")
        p_proc.add_argument("--sync", action="store_true", help="Update the /proc state files")
        p_proc.add_argument("--cat", type=str, help="Read a state file (sys, daemons, islands, tasks)")

        # Snapshot
        p_snap = subparsers.add_parser("snapshot", help="Creation and viewing of system snapshots (APFS CoW / Micro-Snapshots)")
        p_snap.add_argument("action", choices=["create", "list", "micro", "shadow", "rollback", "prune"], help="Snapshot action")
        p_snap.add_argument("--target", type=str, default="", help="Target file for a shadow snapshot or rollback")
        p_snap.add_argument("--id", type=str, default="", help="Snapshot identifier for rollback")
        p_snap.add_argument("-m", "--comment", type=str, default="", help="Snapshot description")

        # Notify
        p_notif = subparsers.add_parser("notify", help="Send a quiet notification to the macOS Notification Center")
        p_notif.add_argument("title", type=str, help="Notification title")
        p_notif.add_argument("message", type=str, help="Notification text")
        p_notif.add_argument("--subtitle", type=str, default="", help="Subtitle")

        # Env
        p_env = subparsers.add_parser("env", help="Runtime regime (Python, Node.js, Git) and installed libraries")
        p_env.add_argument("--json", action="store_true", help="JSON format output")

        # Vacuum
        p_vacuum = subparsers.add_parser("vacuum", help="System sanitizer and cleanup of temporary files (.DS_Store, *.bak, __pycache__)")
        p_vacuum.add_argument("--target", choices=["all", "vault", "pulsar"], default="all", help="Cleanup scope (default: all)")
        p_vacuum.add_argument("--dry-run", action="store_true", help="Scan mode without deleting files")

    @classmethod
    def execute(cls, args: Any) -> int:
        cmd = args.command

        if cmd == "status":
            flags = ["--json"] if getattr(args, "json", False) else []
            res = run_script("system_status.py", flags)
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr, end="")
            auto_log_telemetry("System status check", skill="sys.status")
            return res.get("returncode", 0)

        elif cmd == "boot":
            flags = ["--no-notify"] if getattr(args, "no_notify", False) else []
            res = run_script("boot_engine.py", flags)
            print(res.get("stdout", ""))
            auto_log_telemetry("System boot check", skill="sys.boot")
            return res.get("returncode", 0)

        elif cmd == "proc":
            # Fast in-process sub-millisecond execution (<2ms)
            try:
                from and_os.lib.core import update_procfs, read_sys_stat
                if args.sync:
                    info = update_procfs()
                    print("🟢 ProcFS updated successfully:")
                    print(f"  sys.stat -> {info['disk_free_gb']}GB free, daemons: {sum(1 for d in info['daemons'].values() if d['status'] == 'UP')}/3")
                    auto_log_telemetry("ProcFS sync", skill="sys.proc")
                    return 0
                elif args.cat == "sys":
                    update_procfs()
                    print(read_sys_stat())
                    auto_log_telemetry("ProcFS cat sys", skill="sys.proc")
                    return 0
            except (ImportError, KeyError, OSError, RuntimeError) as err:
                sys.stderr.write(f"[sys_cli:proc] Notice: core procfs unavailable ({err}), delegating to proc_mesh.py\n")

            flags = []
            if args.sync:
                flags.append("--sync")
            elif args.cat:
                flags.extend(["--cat", args.cat])
            res = run_script("proc_mesh.py", flags)
            print(res.get("stdout", ""))
            auto_log_telemetry(f"Proc mesh: {args.cat or 'all'}", skill="sys.proc")
            return res.get("returncode", 0)

        elif cmd == "snapshot":
            if args.action == "prune":
                from and_os.lib.apfs_shadow import prune_shadows, load_retention_config, SHADOW_BASE
                policy = load_retention_config()
                pruned = prune_shadows()
                remaining_mb = 0
                if os.path.isdir(SHADOW_BASE):
                    for root, _, files in os.walk(SHADOW_BASE):
                        for f in files:
                            try:
                                remaining_mb += os.path.getsize(os.path.join(root, f)) / 1048576
                            except OSError:
                                continue  # broken symlink inside an old snapshot
                print(f"Shadow retention (age <= {policy['max_age_days']}d, <= {policy['max_snapshots_per_target']} per target): {pruned} snapshot(s) pruned, vault_shadow now {remaining_mb:.1f} MB")
                auto_log_telemetry(f"Shadow Prune: {pruned} pruned", skill="sys.snapshot")
                return 0
            if args.action in ("shadow", "rollback"):
                from and_os.lib.apfs_shadow import create_shadow_copy, rollback_from_shadow
                if not args.target:
                    print("Error: --target <path> is required for shadow or rollback.", file=sys.stderr)
                    return 1
                if args.action == "shadow":
                    snap = create_shadow_copy(args.target)
                    print(f"APFS Zero-Cost Shadow Snapshot created: {snap}")
                    auto_log_telemetry(f"Shadow Snapshot: {args.target}", skill="sys.snapshot")
                elif args.action == "rollback":
                    ok = rollback_from_shadow(args.target, snapshot_id=args.id if args.id else None)
                    if ok:
                        print(f"APFS Zero-Cost Rollback SUCCESS for: {args.target}")
                        auto_log_telemetry(f"Shadow Rollback: {args.target}", skill="sys.snapshot")
                    else:
                        print(f"Error: No shadow snapshots found for {args.target}", file=sys.stderr)
                        return 1
                return 0

            flags = [args.action]
            if args.comment:
                flags.extend(["-m", args.comment])
            res = run_script("safe_snapshot.py", flags)
            print(res.get("stdout", ""))
            auto_log_telemetry(f"Snapshot: {args.action}", skill="sys.snapshot")
            return res.get("returncode", 0)

        elif cmd == "notify":
            flags = [args.title, args.message]
            if getattr(args, "subtitle", None):
                flags.append(args.subtitle)
            res = run_script("notify_macos.py", flags)
            print(res.get("stdout", ""))
            return res.get("returncode", 0)

        elif cmd == "env":
            flags = ["--build"]
            if getattr(args, "json", False):
                flags.append("--json")
            res = run_script("system_tools_map.py", flags)
            print(res.get("stdout", ""))
            auto_log_telemetry("Runtime environment check", skill="sys.env")
            return res.get("returncode", 0)

        elif cmd == "vacuum":
            flags = ["--target", args.target]
            if getattr(args, "dry_run", False):
                flags.append("--dry-run")
            res = run_script("vacuum_cleaner.py", flags)
            print(res.get("stdout", ""))
            auto_log_telemetry(f"Vacuum cleaner: {args.target}", skill="sys.vacuum")
            return res.get("returncode", 0)

        return 1
