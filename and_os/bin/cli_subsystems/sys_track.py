"""Production tracking subsystem (track command: Ftrack, Weeek).
Modular extraction from sys_cli.py following Clean Architecture (Uncle Bob).
"""

import sys
from typing import Any
from and_os.bin.cli_subsystems.base import BaseSubsystem, run_script, auto_log_telemetry


class TrackSubsystem(BaseSubsystem):
    name = "track"
    description = "Production tracking and synchronization gateway (Ftrack, Weeek)"

    @classmethod
    def register_subparsers(cls, subparsers) -> None:
        p_track = subparsers.add_parser("track", help="Synchronization of production trackers (Ftrack, Weeek, Mattermost)")
        p_track.add_argument("service", choices=["ftrack", "weeek", "mattermost", "all"], help="Target service")
        p_track.add_argument("--project", choices=["mars", "kot", "all"], default="mars", help="Studio project (mars / kot)")
        p_track.add_argument("--report", action="store_true", help="Generate the producer report")
        p_track.add_argument("--gantt", action="store_true", help="Export the data to a Gantt chart")
        p_track.add_argument("--inspect", action="store_true", help="Structure and channel/field audit (Ftrack / Mattermost)")
        p_track.add_argument("--verify", action="store_true", help="Integrity check of the local snapshot (raw_latest)")
        p_track.add_argument("--export", action="store_true", help="Careful staged export from the API")
        p_track.add_argument("--summary", action="store_true", help="Compact summary from the local cache (< 1000 tokens)")
        p_track.add_argument("--channel", type=str, help="Mattermost channel name or filter")
        p_track.add_argument("--search", type=str, help="Search query over messages")
        p_track.add_argument("--json", action="store_true", help="JSON format output")

    @classmethod
    def execute(cls, args: Any) -> int:
        flags = []
        if args.service == "ftrack":
            if getattr(args, "inspect", False):
                script = "ftrack_inspector.py"
                flags.extend(["inspect", "--project", args.project])
            elif getattr(args, "verify", False):
                script = "ftrack_inspector.py"
                flags.extend(["verify-slice", "--project", args.project])
            elif getattr(args, "export", False):
                script = "ftrack_inspector.py"
                flags.extend(["staged-export", "--project", args.project])
            elif args.gantt:
                script = "ftrack_gantt_exporter.py"
                flags.extend(["--project", args.project])
            elif args.report:
                script = "ftrack_report.py"
                flags.extend(["--project", args.project, "--report"])
            elif getattr(args, "summary", False):
                script = "ftrack_report.py"
                flags.extend(["--project", args.project, "--summary"])
            else:
                script = "ftrack_sync.py"
                flags.extend(["--project", args.project])
        elif args.service == "weeek":
            script = "weeek_sync.py"
            if getattr(args, "verify", False):
                flags.extend(["--verify-slice", "--board", args.project])
            else:
                flags.extend(["--board", args.project])
                if getattr(args, "summary", False):
                    flags.append("--summary")
                elif getattr(args, "report", False):
                    flags.append("--export-md")
        elif args.service == "mattermost":
            if getattr(args, "verify", False):
                script = "mattermost_inspector.py"
                flags.extend(["verify-slice", "--project", args.project])
            elif getattr(args, "inspect", False):
                script = "mattermost_inspector.py"
                flags.extend(["inspect", "--project", args.project])
            elif getattr(args, "export", False):
                script = "mattermost_inspector.py"
                flags.extend(["staged-export", "--project", args.project])
            else:
                script = "mattermost_sync.py"
                flags.extend(["--team", args.project])
                if getattr(args, "channel", None):
                    flags.extend(["--channel", args.channel])
                if getattr(args, "search", None):
                    flags.extend(["--search", args.search])
                if getattr(args, "summary", False):
                    flags.append("--summary")
        elif args.service == "all":
            # Cascade synchronization
            res1 = run_script("ftrack_sync.py", ["--project", args.project])
            res2 = run_script("weeek_sync.py", ["--board", args.project])
            print(res1.get("stdout", ""))
            print(res2.get("stdout", ""))
            auto_log_telemetry(f"Production tracking all ({args.project})", skill="sys.track")
            return 0
        else:
            script = "ftrack_sync.py"
            flags.extend(["--project", args.project])

        if getattr(args, "json", False):
            flags.append("--json")

        res = run_script(script, flags)
        print(res.get("stdout", ""), end="")
        if res.get("stderr"):
            print(res["stderr"], file=sys.stderr)
        auto_log_telemetry(f"Production tracking ({args.service} / {args.project})", skill="sys.track")
        return res.get("returncode", 0)
