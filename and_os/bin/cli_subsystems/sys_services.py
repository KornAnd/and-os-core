"""System Services, Daemons, and Domain Bridges Subsystem.
Modular extraction from sys_cli.py following Clean Architecture (Uncle Bob).
Handles daemon, islands, finance, health, telemetry_sync, tasks, skills, skill, event, project, vfs, app, backup, toolchain, sync, state, chunk, taskdb, init, preflight.
"""

import os
import sys
import json
import socket
import subprocess
import time
from typing import Any
from and_os.bin.cli_subsystems.base import BaseSubsystem, run_script, auto_log_telemetry, VAULT_ROOT


def _await_service_settle(state_path: str, svc_id: str, timeout: float,
                          trigger_time_str: str):
    """Closed-loop wait for a manual service run (13.11, no LLM in the middle).

    Polls the supervisor state mesh (written every ~2s by the probe cycle)
    until the service settles: a state STRICTLY NEWER than the trigger
    moment (second-granularity, lexicographic = chronological for the
    fixed format) shows the id with the pid released and an idle status.
    Returns the final service info dict, or None on timeout.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with open(state_path, encoding="utf-8") as handle:
                mesh = json.load(handle)
        except (OSError, ValueError):
            mesh = {}
        mesh_ts = mesh.get("timestamp", "")
        svc = (mesh.get("services") or {}).get(svc_id)
        if svc is not None and mesh_ts > trigger_time_str:
            idle = svc.get("status") in ("ON_DEMAND", "SCHEDULED", "DISABLED")
            if idle and svc.get("pid") is None:
                return svc
        time.sleep(1.0)
    return None


class ServicesSubsystem(BaseSubsystem):
    name = "services"
    description = "LaunchAgents daemons, islands registry, domain bridges, health, finance, and background sync"

    @classmethod
    def register_subparsers(cls, subparsers) -> None:
        import argparse

        # daemon
        p_daemon = subparsers.add_parser("daemon", help="The control of the macOS background daemons and the Pulsar services (Rule #28)")
        p_daemon.add_argument("action", choices=["status", "restart", "trigger"], help="The action over the daemons (trigger = a closed manual run of an on-demand service)")
        p_daemon.add_argument("pos_target", nargs="?", default="", help="The service name (the positional argument)")
        p_daemon.add_argument("--target", type=str, default="", help="The service name (the flag)")
        p_daemon.add_argument("--timeout", type=float, default=600.0, help="The max wait for a trigger run to settle, in seconds (default 600)")

        # islands
        p_islands = subparsers.add_parser("islands", help="The summary of the 9 logical islands and the detailed passport (--info <1-9>)")
        p_islands.add_argument("--info", type=int, choices=range(1, 10), help="The island number (1-9)")

        # telemetry_sync
        p_telemetry_sync = subparsers.add_parser("telemetry_sync", help="The weekly deep analysis and the synchronization of the telemetry_sync Connect biometrics")
        p_telemetry_sync.add_argument("--mock", action="store_true", help="Use the verified profile dataset")
        p_telemetry_sync.add_argument("--json", action="store_true", help="The output in the JSON format")

        # health
        p_health = subparsers.add_parser("health", help="The unified cross synthesis of the health contour")
        p_health.add_argument("--patient", choices=["andrey", "misha", "yulia", "pavel", "mom"], help="The patient ID")
        p_health.add_argument("--summary", action="store_true", help="The compressed report over the patient")
        p_health.add_argument("--check", action="store_true", help="The integrity check of the base")
        p_health.add_argument("--json", action="store_true", help="The output in the JSON format")

        # finance
        p_fin = subparsers.add_parser("finance", help="The slice of the investment capital")
        p_fin.add_argument("--broker", choices=["broker_account", "alfa"], help="The filter by the broker")
        p_fin.add_argument("--summary", action="store_true", help="The compressed Net Worth summary")
        p_fin.add_argument("--check", action="store_true", help="The integrity check of the base")
        p_fin.add_argument("--json", action="store_true", help="The output in the JSON format")

        # tasks
        p_tasks = subparsers.add_parser("tasks", help="The instant production pulse of the studio and the operational control of the tasks")
        p_tasks.add_argument("--pulse", action="store_true", help="The compressed operational pulse")
        p_tasks.add_argument("--project", choices=["mars", "kot", "pm", "Studio"], help="The filter by the project")
        p_tasks.add_argument("--complete", default="", help="Mark the task as completed")
        p_tasks.add_argument("--check", action="store_true", help="The check of the SQLite tasks base")
        p_tasks.add_argument("--json", action="store_true", help="The output in the JSON format")

        # vfs
        p_vfs = subparsers.add_parser("vfs", help="The reactive virtual file system")
        p_vfs.add_argument("--status", action="store_true", help="The VFS status and the background daemon")
        p_vfs.add_argument("--pulsar", action="store_true", help="The matrix of the Pulsar Space services")
        p_vfs.add_argument("--find", type=str, help="The files search by the SQLite index")
        p_vfs.add_argument("--island", type=str, help="The filter by the island (1-8)")
        p_vfs.add_argument("--ext", type=str, help="The filter by the file extension")
        p_vfs.add_argument("--sync", action="store_true", help="The VFS index synchronization")
        p_vfs.add_argument("--start", action="store_true", help="The launch of the VFS background daemon")
        p_vfs.add_argument("--stop", action="store_true", help="The stop of the VFS background daemon")

        # event
        p_evt = subparsers.add_parser("event", help="The event bus of the AnD os")
        p_evt.add_argument("action", choices=["emit", "list", "clear"], help="The action over the event bus")
        p_evt.add_argument("type", nargs="?", default="EVENT", help="The event type")
        p_evt.add_argument("payload", nargs="?", default="{}", help="The payload")
        p_evt.add_argument("--source", default="cli", help="The event source")
        p_evt.add_argument("-n", "--count", type=int, default=20, help="The count of the events")
        p_evt.add_argument("--json", action="store_true", help="The output in the JSON")

        # project
        p_proj = subparsers.add_parser("project", help="The control of the projects registry (Pulsar / Xcode)")
        p_proj.add_argument("subaction", nargs="?", choices=["list", "pulsar", "xcode"], default="list")
        p_proj.add_argument("--scan", action="store_true", help="Scan the applications")
        p_proj.add_argument("--sync", action="store_true", help="Synchronize the passports")
        p_proj.add_argument("--name", help="The name of the service or the game")
        p_proj.add_argument("--desc", help="The description of the project")
        p_proj.add_argument("--category", default="Web Dashboard")
        p_proj.add_argument("--type", default="iOS Game / SpriteKit")
        p_proj.add_argument("--port", type=int, help="The network TCP port")
        p_proj.add_argument("--status", choices=["production", "active", "in_development", "concept"], default="active")
        p_proj.add_argument("--repo", help="The path to the sources")
        p_proj.add_argument("--source", help="The path to the Xcode sources")
        p_proj.add_argument("--tags", help="The tags separated by a comma")

        # app
        p_app = subparsers.add_parser("app", help="The control of the link with the external web applications")
        p_app.add_argument("--blueprint", type=str, help="Generate the architectural prompt-passport")

        # backup
        p_bup = subparsers.add_parser("backup", help="The full backup of the Obsidian Vault storage")
        p_bup.add_argument("--status", action="store_true", help="Check the status of the last backup")

        # toolchain
        p_tc = subparsers.add_parser("toolchain", help="The control and the conformity check of the toolchain (Rule #68)")
        p_tc.add_argument("action", choices=["status", "check", "sync"], default="status", nargs="?")

        # skills
        p_skills = subparsers.add_parser("skills", help="The parallel multithreaded audit and the control of the skills stack (SOS)")
        p_skills.add_argument("--probe", action="store_true", help="Launch the canary self-checks")
        p_skills.add_argument("--dormancy", action="store_true", help="The revision of the skills inactivity")
        p_skills.add_argument("--search", type=str, help="The search of the external agent skills")
        p_skills.add_argument("--inspect", type=str, help="The inspection of the external skill")
        p_skills.add_argument("--json", action="store_true", help="The output in the JSON")

        # skill
        p_skill = subparsers.add_parser("skill", help="The unified microkernel gateway to the skill modules")
        p_skill.add_argument("skill_action", choices=["run", "ref", "info", "pipe", "list", "lint", "verify"])
        p_skill.add_argument("skill_name", nargs="?")
        p_skill.add_argument("consumer", nargs="?")
        p_skill.add_argument("--topic")
        p_skill.add_argument("--list", action="store_true")
        p_skill.add_argument("--json", action="store_true")
        p_skill.add_argument("extra_args", nargs=argparse.REMAINDER)

    @classmethod
    def execute(cls, args: Any) -> int:
        cmd = args.command

        if cmd == "telemetry_sync":
            flags = []
            if getattr(args, "mock", False):
                flags.append("--mock")
            if getattr(args, "json", False):
                flags.append("--json")
            res = run_script("telemetry_sync_deep_sync.py", flags)
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry("telemetry_sync weekly deep sync", skill="sys.telemetry_sync")
            return res.get("returncode", 0)

        elif cmd == "health":
            flags = []
            if getattr(args, "check", False):
                res = run_script("health_bridge.py", ["check"])
            elif getattr(args, "summary", False) or getattr(args, "patient", None):
                pid = getattr(args, "patient", None) or "andrey"
                bridge_flags = ["summary", "--patient", pid]
                if getattr(args, "json", False):
                    bridge_flags.append("--json")
                res = run_script("health_bridge.py", bridge_flags)
            else:
                if getattr(args, "json", False):
                    flags.append("--json")
                res = run_script("health_orchestrator_engine.py", flags)
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry("Health command execution", skill="sys.health")
            return res.get("returncode", 0)

        elif cmd == "finance":
            flags = []
            if getattr(args, "check", False):
                flags.append("check")
            else:
                flags.append("summary")
                if getattr(args, "broker", None):
                    flags.extend(["--broker", args.broker])
                if getattr(args, "json", False):
                    flags.append("--json")
            res = run_script("finance_bridge.py", flags)
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry("Finance summary check", skill="sys.finance")
            return res.get("returncode", 0)

        elif cmd == "tasks":
            flags = []
            if getattr(args, "check", False):
                flags.append("check")
            elif getattr(args, "complete", ""):
                flags.extend(["complete", args.complete])
                if getattr(args, "project", None):
                    flags.extend(["--project", args.project])
            else:
                flags.append("pulse")
                if getattr(args, "project", None):
                    flags.extend(["--project", args.project])
                if getattr(args, "json", False):
                    flags.append("--json")
            res = run_script("tasks_bridge.py", flags)
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry(f"Tasks pulse check ({getattr(args, 'project', 'all')})", skill="sys.tasks")
            return res.get("returncode", 0)

        elif cmd == "vfs":
            flags = []
            if getattr(args, "status", False):
                flags.append("--status")
            elif getattr(args, "pulsar", False):
                flags.append("--pulsar")
            elif getattr(args, "find", None):
                flags.extend(["--find", args.find])
                if getattr(args, "island", None):
                    flags.extend(["--island", args.island])
                if getattr(args, "ext", None):
                    flags.extend(["--ext", args.ext])
            elif getattr(args, "sync", False):
                flags.append("--sync")
            elif getattr(args, "start", False):
                flags.append("--start")
            elif getattr(args, "stop", False):
                flags.append("--stop")
            else:
                flags.append("--status")
            res = run_script("vfs_bridge.py", flags)
            print(res.get("stdout", ""), end="")
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            auto_log_telemetry("VFS command execution", skill="sys.vfs")
            return res.get("returncode", 0)

        elif cmd == "daemon":
            target_name = getattr(args, "pos_target", "") or getattr(args, "target", "")
            sock_candidates = [
                os.path.expanduser("~/.and_os/var/run/supervisor.sock"),
                os.path.join(VAULT_ROOT, "and_os/var/run/supervisor.sock")
            ]
            sup_sock = next((p for p in sock_candidates if os.path.exists(p)), None)
            
            if sup_sock:
                try:
                    s_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    s_sock.settimeout(5.0)
                    s_sock.connect(sup_sock)
                    # The supervisor IPC speaks the plain-text protocol
                    # (and_supervisor._dispatch_ipc_command): STATUS | RESTART [id] | TRIGGER <id>
                    if args.action == "trigger":
                        if not target_name:
                            s_sock.close()
                            sys.stderr.write("[sys_services] Error: trigger requires the service id (e.g. proc_mesh)\n")
                            return 2
                        # Trigger moment BEFORE the wire send: the settle
                        # state must be strictly newer than this instant.
                        trigger_time_str = time.strftime("%Y-%m-%d %H:%M:%S")
                        s_sock.sendall(f"TRIGGER {target_name}".encode("utf-8"))
                        data = s_sock.recv(65536)
                        resp = json.loads(data.decode("utf-8"))
                        s_sock.close()
                        if resp.get("result") == "NOT_FOUND":
                            sys.stderr.write(f"[sys_services] Error: unknown service '{target_name}'\n")
                            return 1
                        print(f"=== \u25b6\ufe0f The manual run of the on-demand service {target_name} (the closed software contour) ===")
                        state_path = os.path.join(os.path.expanduser("~/.and_os"), "var", "supervisor_state.json")
                        svc = _await_service_settle(state_path, target_name,
                                                    timeout=args.timeout,
                                                    trigger_time_str=trigger_time_str)
                        if svc is None:
                            sys.stderr.write(f"[sys_services] Timeout: {target_name} did not settle within {args.timeout:.0f}s (the run may still finish, check the daemon grid)\n")
                            return 1
                        code = svc.get("last_exit_code")
                        if code == 0:
                            print(f"  \u2705 {target_name} finished: exit 0 (status {svc.get('status')})")
                            auto_log_telemetry(f"Daemon supervisor trigger {target_name} (exit 0)", skill="sys.daemon")
                            return 0
                        sys.stderr.write(f"[sys_services] {target_name} finished with exit {code} (status {svc.get('status')}) — the run output is in ~/.and_os/logs/{target_name}.err.log\n")
                        auto_log_telemetry(f"Daemon supervisor trigger {target_name} (exit {code})", skill="sys.daemon")
                        return 1
                    if args.action == "restart":
                        wire_cmd = f"RESTART {target_name}".strip() if target_name else "RESTART"
                    else:
                        wire_cmd = "STATUS"
                    s_sock.sendall(wire_cmd.encode("utf-8"))
                    data = s_sock.recv(65536)
                    resp = json.loads(data.decode("utf-8"))
                    s_sock.close()
                    if "error" in resp:
                        sys.stderr.write(f"[sys_services] Supervisor IPC error: {resp['error']}\n")
                        return 1
                    if args.action == "restart":
                        print(f"=== 🔄 The restart of the background daemon {target_name or 'all'} via the supervisor IPC ===")
                        print(f"  [OK] {resp.get('result', 'OK')}")
                    else:
                        print(f"=== ⚙️ AnD os Master Supervisor Daemon Grid ===")
                        sup_metrics = resp.get("supervisor") or {}
                        if sup_metrics.get("uptime_sec"):
                            print(f"  (supervisor: up {int(sup_metrics['uptime_sec'])}s, "
                                  f"cpu {sup_metrics.get('cpu_pct', 0)}%, rss {sup_metrics.get('rss_mb', 0)}MB)")
                        for s_info in resp.get("services", []):
                            st = s_info.get("status", "?")
                            st_icon = "🟢" if st in ("HEALTHY", "UP", "SCHEDULED", "ON_DEMAND", "RUNNING") else "🔴"
                            bits = [f"PID {s_info.get('pid', '-')}", f"port {s_info.get('port') or '-'}",
                                    f"fail {s_info.get('fail_count', 0)}"]
                            if s_info.get("uptime_sec") is not None:
                                bits.append(f"up {int(s_info['uptime_sec'])}s")
                            if s_info.get("next_run"):
                                bits.append(f"next {s_info['next_run']}")
                            print(f"  • {st_icon} {s_info.get('id', '?')}: {st} ({', '.join(bits)})")
                    auto_log_telemetry(f"Daemon supervisor {args.action}", skill="sys.daemon")
                    return 0
                except (OSError, ValueError) as err:
                    sys.stderr.write(f"[sys_services] Notice: the supervisor socket was unavailable, the per-service fallback is used: {err}\n")

            target_services = [
                {"id": "ftrack_mars", "port": 8087, "name": "Ftrack Mars Gantt", "plist": "com.and_os.ftrack_gantt"},
                {"id": "ftrack_kot", "port": 8092, "name": "Ftrack Kot Gantt", "plist": "com.and_os.kot_gantt"},
                {"id": "vfs", "port": None, "name": "VFS Reactive Daemon", "plist": "com.and_os.vfs_daemon"},
                {"id": "terminal", "port": 8099, "name": "AND_Terminal Web GUI", "plist": "com.and_os.terminal"}
            ]

            if args.action == "status":
                print("=== ⚙️ The background services and the daemons of the macOS (AnD os LaunchAgents) ===")
                for s in target_services:
                    status_port = "⚪ N/A"
                    if s["port"]:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(0.2)
                        res = sock.connect_ex(("127.0.0.1", s["port"]))
                        sock.close()
                        status_port = f"🟢 LISTEN (127.0.0.1:{s['port']})" if res == 0 else "🔴 DOWN"
                    chk = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
                    in_launchctl = s["plist"] in chk.stdout
                    status_agent = "🟢 LOADED" if in_launchctl else "⚪ NOT LOADED"
                    print(f"  • {s['name']} [{s['plist']}]: Daemon {status_agent} | Port: {status_port}")

            elif args.action == "restart":
                print(f"=== 🔄 The restart of the background daemon {target_name or 'all'} ===")
                targets = [s for s in target_services if not target_name or target_name in s["id"] or target_name in s["plist"]]
                if not targets:
                    print(f"  [!] The service was not found by the filter '{target_name}'", file=sys.stderr)
                    return 1
                for s in targets:
                    plist_path = os.path.expanduser(f"~/Library/LaunchAgents/{s['plist']}.plist")
                    if os.path.exists(plist_path):
                        subprocess.run(["launchctl", "unload", plist_path], capture_output=True)
                        res = subprocess.run(["launchctl", "load", plist_path], capture_output=True)
                        if res.returncode == 0:
                            print(f"  [OK] The daemon {s['name']} was successfully restarted via the launchctl.")
                        else:
                            print(f"  [!] The restart error of {s['name']}: {res.stderr.strip()}", file=sys.stderr)
                    else:
                        print(f"  [!] The Plist file was not found: {plist_path}", file=sys.stderr)
            auto_log_telemetry(f"Daemon {args.action}", skill="sys.daemon")
            return 0

        elif cmd == "islands":
            from and_os.bin.sys_cli import cmd_islands
            cmd_islands(args)
            return 0

        elif cmd == "skills":
            from and_os.bin.sys_cli import cmd_skills
            cmd_skills(args)
            return 0

        elif cmd == "skill":
            from and_os.bin.sys_cli import cmd_skill
            cmd_skill(args)
            return 0

        elif cmd == "event":
            from and_os.bin.sys_cli import cmd_event
            cmd_event(args)
            return 0

        elif cmd == "project":
            from and_os.bin.sys_cli import cmd_project
            cmd_project(args)
            return 0

        elif cmd == "app":
            from and_os.bin.sys_cli import cmd_app
            cmd_app(args)
            return 0

        elif cmd == "backup":
            from and_os.bin.sys_cli import cmd_backup
            cmd_backup(args)
            return 0

        elif cmd == "toolchain":
            from and_os.bin.sys_cli import cmd_toolchain
            cmd_toolchain(args)
            return 0

        return 1
